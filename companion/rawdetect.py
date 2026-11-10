"""Erkennungsbild aus dem RAW.

Der Export fuer die Anzeige ist bearbeitet (Inversion, Tonkurve). Bei dunklen Bildern liegen Filmrand und
Bild dort beide im Schwarz, die Kante steht nicht mehr in der Datei. Im RAW sind sie getrennt: linear
entwickelt, logarithmiert (Dichte) und ab dem Filmrand gestreckt, wird die Kante sichtbar.

Das Erkennungsbild hat Ausrichtung und Seitenverhaeltnis des Exports, damit der Crop fuer beide gilt. Ob
Negativ oder Dia, entscheidet die Rolle: Die Erkennung sucht den Sprung vom dunklen Filmrand ins helle
Bild, und nur die richtige Polung liefert ueber die Rolle geschlossene Kanten.
"""
import os

import cv2
import numpy as np

import frame_edges

LONG = frame_edges.LONG
DENSITY_RANGE = 0.4         # Dichtestufen (log10) ab Filmrand, die auf den Grauwertumfang fallen
BASE_PCT = 5                # Perzentil des Erkennungsbilds, das als Filmrand gilt (dunkelste Flaeche)
BASE_LEVEL = 0.1            # Grauwert des Filmrands (Anteil), laesst Platz fuer Rauschen nach unten
FLOOR = 2e-4                # unter diesem linearen Wert zaehlt nur noch Rauschen
MATCH_SIDE = 96             # Kantenlaenge der Verkleinerung fuer den Abgleich der Ausrichtung
MATCH_INSET = 0.15          # Rand, der beim Abgleich wegfaellt: der Filmrand sieht in jeder Lage gleich aus
MATCH_MIN = 0.5             # Mindest-Korrelation mit dem Export
MATCH_GAP = 0.02            # Vorsprung vor der zweitbesten Lage
ASPECT_TOL = 0.005          # so weit darf das Seitenverhaeltnis des Exports vom RAW abweichen
NEG, POS = "neg", "pos"
POLARITIES = (NEG, POS)
SAMPLE = 8                  # Bilder je Rolle fuer die Polung


def available():
    try:
        import rawpy  # noqa: F401
    except ImportError:
        return False
    return True


def linear(raw_path):
    """RAW linear und ohne Drehung als Graubild 0..1 (halbe Aufloesung)."""
    import rawpy
    with rawpy.imread(raw_path) as r:
        rgb = r.postprocess(gamma=(1, 1), no_auto_bright=True, output_bps=16, half_size=True,
                            user_flip=0, use_camera_wb=True)
    return rgb.astype(np.float32).mean(axis=2) / 65535.0


def _variants(img):
    """Die acht Lagen eines Bilds: vier Drehungen, je gespiegelt und ungespiegelt."""
    for mirrored in (img, img[:, ::-1]):
        for k in range(4):
            yield np.rot90(mirrored, k)


def _thumb(img):
    """Bildmitte, verkleinert und als Vektor."""
    h, w = img.shape
    dy, dx = int(h * MATCH_INSET), int(w * MATCH_INSET)
    mid = np.ascontiguousarray(img[dy:h - dy, dx:w - dx], dtype=np.float32)
    return cv2.resize(mid, (MATCH_SIDE, MATCH_SIDE), interpolation=cv2.INTER_AREA).ravel()


def orient(lin, export_gray):
    """Bringt das lineare Bild in Lage und Groesse des Exports (lange Kante LONG).

    Der Export kann invertiert sein (Negativ), darum zaehlt der Betrag der Korrelation.
    -> Bild oder None, wenn keine Lage klar passt oder der Export einen anderen Ausschnitt zeigt (im
    RAW-Entwickler gedreht oder entzerrt: dann gilt ein Crop aus dem RAW nicht fuer den Export)."""
    eh, ew = export_gray.shape
    aspect, raw_aspect = max(ew, eh) / min(ew, eh), max(lin.shape) / min(lin.shape)
    if abs(aspect / raw_aspect - 1) > ASPECT_TOL:
        return None
    ref = _thumb(export_gray)
    scored = []
    for v in _variants(lin):
        if (v.shape[0] > v.shape[1]) != (eh > ew):
            continue
        scored.append((abs(float(np.corrcoef(_thumb(np.sqrt(v)), ref)[0, 1])), v))
    scored.sort(key=lambda s: -s[0])
    if not scored or scored[0][0] < MATCH_MIN:
        return None
    if len(scored) > 1 and scored[0][0] - scored[1][0] < MATCH_GAP:
        return None
    shrink = LONG / max(ew, eh)
    size = (round(ew * shrink), round(eh * shrink)) if shrink < 1 else (ew, eh)
    return cv2.resize(np.ascontiguousarray(scored[0][1]), size, interpolation=cv2.INTER_AREA)


def stretch(lin, polarity):
    """Dichtebild: Filmrand dunkel, Bild heller, DENSITY_RANGE ab Filmrand auf 0..255."""
    v = np.log10(lin + FLOOR)
    if polarity == NEG:
        v = -v
    base = np.percentile(v, BASE_PCT)
    return (np.clip((v - base) / DENSITY_RANGE + BASE_LEVEL, 0, 1) * 255).astype(np.uint8)


def path_for(out_base, polarity):
    return f"{out_base}.{polarity}.png"


def cached(out_base, raw):
    """Polung, deren Erkennungsbild schon vorliegt und nicht aelter ist als das RAW, sonst None."""
    for pol in POLARITIES:
        p = path_for(out_base, pol)
        if os.path.exists(p) and os.path.getmtime(p) >= os.path.getmtime(raw):
            return pol
    return None


def write(item):
    """Schreibt beide Polungen eines Bilds. item = (raw, export, out_base). -> True, wenn geschrieben."""
    raw, export, out_base = item
    for pol in POLARITIES:      # Reste einer frueheren Rechnung
        if os.path.exists(path_for(out_base, pol)):
            os.remove(path_for(out_base, pol))
    try:
        export_gray = cv2.imread(export, cv2.IMREAD_GRAYSCALE)
        img = orient(linear(raw), export_gray) if export_gray is not None else None
    except Exception:       # noqa: BLE001 - unlesbares RAW: der Export bleibt das Erkennungsbild
        return False
    if img is None:
        return False
    os.makedirs(os.path.dirname(out_base), exist_ok=True)
    for pol in POLARITIES:
        cv2.imwrite(path_for(out_base, pol), stretch(img, pol))
    return True


def _evidence(paths):
    items = []
    for p in paths:
        try:
            items.append(frame_edges.measure((p, None, False)))
        except Exception:   # noqa: BLE001
            continue
    shape = (items[0]["w"], items[0]["h"]) if items else None
    items = [it for it in items if (it["w"], it["h"]) == shape]
    roll = frame_edges.roll_size(items, None) if items else None
    return roll["score_w"] + roll["score_h"] if roll else 0.0


def polarity(out_bases):
    """Polung einer Rolle: die mit der staerkeren Kantenevidenz ueber eine Stichprobe."""
    step = max(1, len(out_bases) // SAMPLE)
    sample = out_bases[::step][:SAMPLE]
    return max(POLARITIES, key=lambda pol: _evidence([path_for(b, pol) for b in sample]))


def settle(out_bases):
    """Legt die Polung einer Rolle fest und loescht die Bilder der anderen. -> Polung oder None.

    None, wenn ein Bild der Rolle fehlt. Liegt je Bild nur noch eine Polung vor (frueherer Lauf), gilt sie."""
    have = [{pol for pol in POLARITIES if os.path.exists(path_for(b, pol))} for b in out_bases]
    common = set.intersection(*have) if have else set()
    if not common:
        return None
    pol = polarity(out_bases) if len(common) > 1 else common.pop()
    for b, pols in zip(out_bases, have):
        for other in pols - {pol}:
            os.remove(path_for(b, other))
    return pol

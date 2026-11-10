"""Rahmenkanten je Rolle: Bildfenster aus aufsummierter Kantenevidenz.

Das Bildfenster der Kamera ist fuer alle Bilder einer Rolle gleich gross. Darum wird je Bild keine Box gesucht,
sondern nur gemessen, wie geschlossen an jeder Stelle eine Kante dunkel->hell ueber die ganze Kantenlaenge laeuft
(Bildinhalt erzeugt Spruenge in einzelnen Abschnitten, die Rahmenkante in allen). Die Rahmengroesse der Rolle liegt
dort, wo sich Kantenpaare ueber alle Bilder aufsummieren; je Bild bleibt dann nur die Lage.

    Evidenz einer Bildzeile quer ueber den Film (schematisch)

    rise  ___|_____________|___________    | = Sprung dunkel->hell (Filmrand -> Bild)
    fall  _____________|___________|___    | = Sprung hell->dunkel (Bild -> Filmrand)
             ^---- W ----^                  Paar (rise, fall) im Abstand W = Rahmen

Ablauf (siehe ``detect``): measure je Bild -> Rollengroesse -> remeasure je Bild ueber die volle Kantenlaenge ->
Rollengroesse fein -> Lage je Bild (``_finish_roll``). Koordinaten intern: lange Bildkante waagerecht (Filmtransport), LONG px.
"""
import cv2
import numpy as np

LONG = 2000                  # Arbeitsaufloesung, lange Kante in px
SEGMENTS = 24                # Abschnitte entlang einer Kante
STEP_HALF = 4                # halbe Fensterbreite des Sprungs in px
GAMMA = 0.5                  # hebt Spruenge im Dunkeln (Filmrand gegen Schatten)
GAMMA_OFFSET = 4.0           # begrenzt die Verstaerkung im abgesoffenen Schwarz, dort ist nur Rauschen
STEP_FULL = 4.0              # Sprunghoehe (nach Gamma), ab der ein Abschnitt voll zaehlt
SHARP_FULL = 64.0            # ... fuer die Lage der Kante: spaet gedeckelt, das Maximum liegt auf der Kante
REFINE_REACH = STEP_HALF + 1 # so weit darf die Lage dabei wandern (px)
BORDER_EVIDENCE = 0.12       # Dateirand als schwache Kante: reicht der Rahmen bis an den Rand, endet der Crop dort
CENTER_BAND = (0.3, 0.7)     # erster Durchlauf: nur die Bildmitte liegt sicher im Rahmen
TILTS = tuple(sorted(np.round(np.arange(-2.0, 2.01, 0.2), 1), key=abs))   # Grad; 0 zuerst, gewinnt bei Gleichstand
EDGE_MARGIN = 12             # zweiter Durchlauf: Abstand von den Ecken des Rahmens

PITCH_MM = 4.7625            # Lochabstand 35-mm-Film
# (Name, Seitenverhaeltnis von, bis, lange Kante in mm von, bis). Gemessene Bildfenster auf 71 Rollen:
# 36,1-37,1 x 24,1-24,6 mm (3:2), 24,9-25,2 x 24,1-24,3 mm (quadratisch belichteter Kleinbildfilm).
FORMATS = (("3:2", 1.48, 1.525, 35.2, 37.8), ("square", 1.0, 1.07, 23.6, 26.0))
SHORT_MM = (23.5, 25.4)
GATE_MM = (36.5, 24.35)      # Nenngroesse; entscheidet nur, wo die Kanten nichts sagen
GATE_TOL_MM = (1.0, 0.7)
PRIOR_WEIGHT = 0.05
SQUARE_FACTOR = 1.3          # quadratisch gilt nur bei klar besserer Evidenz als 3:2
SQUARE_EXTRA = 0.05
SIZE_RANGE = (0.5, 0.55)     # kleinste Rahmengroesse relativ zur Datei (lang, kurz), ohne Massstab
FINE_REACH = 25              # Feinsuche der Rollengroesse nach dem zweiten Durchlauf, +/- px

SIZE_SLACK = 6               # so weit darf ein Bild ohne Kosten von der Rollengroesse abweichen (px)
FREE_REACH = 0.04            # ein klar gesehenes Kantenpaar darf bis zu diesem Anteil abweichen ...
FREE_COST = 0.01             # ... und zahlt dafuer je px
FREE_MIN = 0.4               # ... wenn beide Kanten mindestens so deutlich sind
STRONG = 0.3                 # Kante gilt als gesehen
WEAK = 0.2                   # darunter traegt eine Kante die Lage nicht
POLARITY_SAMPLE = 8          # Bilder je Rolle, an denen die Polung entschieden wird
POLARITY_LEAD = 2.0          # so viel staerker muss die umgekehrte Polung sein, sonst bleibt es beim Bild, wie es ist
POLARITY_MIN = 0.5           # und mindestens diese Evidenz haben (Summe beider Achsen); verschleierte Rolle: 0,27 gegen 0,17
ROLL_MIN_N = 3               # Bilder mit gesehenen Kanten, ab denen die Rolle eine Lage vorgibt


def load(path, invert=False):
    """Graubild fuer die Messung. -> (gamma, tr, scale, (breite, hoehe) der Datei)

    tr: Datei ist hochkant und wurde gestuerzt. scale: Datei-px je Arbeits-px. invert: Bild umkehren (nicht
    invertiertes Negativ: der Filmrand ist dort heller als das Bild, gemessen wird der Sprung ins Helle)."""
    gray = cv2.imread(path, cv2.IMREAD_GRAYSCALE)
    if gray is None:
        raise FileNotFoundError(f"Bild konnte nicht geladen werden: {path}")
    if invert:
        gray = 255 - gray
    size = (gray.shape[1], gray.shape[0])
    shrink = LONG / max(gray.shape)
    if shrink < 1:
        gray = cv2.resize(gray, None, fx=shrink, fy=shrink, interpolation=cv2.INTER_AREA)
    tr = gray.shape[0] > gray.shape[1]
    if tr:
        gray = gray.T
    gray = cv2.GaussianBlur(np.ascontiguousarray(gray).astype(np.float32), (0, 0), 1.0)
    gamma = 255.0 * ((gray + GAMMA_OFFSET) / (255.0 + GAMMA_OFFSET)) ** GAMMA
    return gamma, tr, (1 / shrink if shrink < 1 else 1.0), size


def _steps(gray, r0, r1):
    """Sprunghoehe je Abschnitt und Spalte fuer senkrechte Kanten aus den Zeilen r0:r1.
    -> (SEGMENTS x Breite, Mitte jedes Abschnitts in px) oder (None, None), wenn zu wenig Zeilen bleiben."""
    w = gray.shape[1]
    r0, r1 = max(0, int(r0)), min(gray.shape[0], int(r1))
    if r1 - r0 < SEGMENTS:
        return None, None

    cuts = np.linspace(r0, r1, SEGMENTS + 1).astype(int)
    prof = np.stack([gray[a:b].mean(axis=0) for a, b in zip(cuts[:-1], cuts[1:])])
    cs = np.concatenate([np.zeros((SEGMENTS, 1), np.float32), np.cumsum(prof, axis=1)], axis=1)
    b = STEP_HALF
    x = np.arange(b, w - b)
    step = np.zeros((SEGMENTS, w), np.float32)
    step[:, b:w - b] = (cs[:, x + b] - 2 * cs[:, x] + cs[:, x - b]) / b
    return step, (cuts[:-1] + cuts[1:]) / 2.0


def _evidence(step, mids, slope):
    """Kantenevidenz aus den Spruengen, entlang einer um ``slope`` (px je px) geneigten Kante gelesen.
    -> (rise, fall, rise_sharp, fall_sharp), Werte 0..1; die Lage gilt fuer die Mitte der Kante.

    rise/fall sagen, *ob* eine Kante da ist: frueh gedeckelt, damit ein schwacher Sprung ueber die ganze Laenge mehr
    zaehlt als ein starker in einem Abschnitt. Um eine klare Kante sind sie dadurch mehrere px breit gleich hoch. *Wo*
    sie liegt, sagen die spaet gedeckelten rise_sharp/fall_sharp (siehe ``_refine``)."""
    w = step.shape[1]
    if slope:
        shift = np.rint(slope * (mids - mids.mean())).astype(int)
        cols = np.clip(np.arange(w)[None, :] + shift[:, None], 0, w - 1)
        step = np.take_along_axis(step, cols, axis=1)

    rise = np.clip(step, 0, STEP_FULL).mean(axis=0) / STEP_FULL
    fall = np.clip(-step, 0, STEP_FULL).mean(axis=0) / STEP_FULL
    rise_sharp = np.clip(step, 0, SHARP_FULL).mean(axis=0) / SHARP_FULL
    fall_sharp = np.clip(-step, 0, SHARP_FULL).mean(axis=0) / SHARP_FULL

    # Dateirand: was in den aeussersten px liegt, zaehlt am Rand selbst
    b = STEP_HALF
    rise[0] = max(float(rise[:b + 1].max()), BORDER_EVIDENCE)
    fall[w - 1] = max(float(fall[w - b - 1:].max()), BORDER_EVIDENCE)
    rise[1:b + 1] = 0
    fall[w - b - 1:w - 1] = 0
    return rise, fall, rise_sharp, fall_sharp


def evidence(gray, r0, r1, slope=0.0):
    """Kantenevidenz senkrechter Kanten aus den Zeilen r0:r1. -> (rise, fall), je Laenge Bildbreite, Werte 0..1.

    rise[x]: mittlerer gedeckelter Sprung dunkel->hell nach rechts ueber SEGMENTS Abschnitte der Kante."""
    step, mids = _steps(gray, r0, r1)
    if step is None:
        zero = np.zeros(gray.shape[1], np.float32)
        return zero, zero.copy()
    return _evidence(step, mids, slope)[:2]


def _both_axes(gray, rows, cols):
    """Evidenz beider Achsen bei der Schraeglage, unter der die Kanten am geschlossensten stehen.

    Der Filmstreifen liegt selten genau gerade; eine um 0,5 Grad geneigte Kante laeuft ueber ihre Laenge 10 px weit
    und zerfiele sonst in Abschnitte, die sich nicht decken. Ein Winkel je Bild (der Rahmen ist starr): senkrechte
    Kanten neigen sich um -tan, waagerechte um +tan."""
    sx, mx = _steps(gray, *rows)
    sy, my = _steps(np.ascontiguousarray(gray.T), *cols)
    if sx is None or sy is None:
        h, w = gray.shape
        out = {k: np.zeros(w, np.float32) for k in ("xr", "xf", "xrs", "xfs")}
        out.update({k: np.zeros(h, np.float32) for k in ("yr", "yf", "yrs", "yfs")})
        return dict(out, tilt=0.0)

    best = None
    for deg in TILTS:
        t = float(np.tan(np.radians(deg)))
        xr, xf, xrs, xfs = _evidence(sx, mx, -t)
        yr, yf, yrs, yfs = _evidence(sy, my, t)
        total = float(xrs.max() + xfs.max() + yrs.max() + yfs.max())     # am schaerfsten, wenn der Winkel stimmt
        if best is None or total > best[0] + 1e-6:
            best = (total, {"xr": xr, "xf": xf, "xrs": xrs, "xfs": xfs,
                            "yr": yr, "yf": yf, "yrs": yrs, "yfs": yfs, "tilt": float(deg)})
    return best[1]


def _size_ranges(w, h, mm_px):
    """Rahmengroessen (lang, kurz) in px, die fuer die Rolle in Frage kommen."""
    if not mm_px:
        return np.arange(int(SIZE_RANGE[0] * w), w), np.arange(int(SIZE_RANGE[1] * h), h)
    lo = min(f[3] for f in FORMATS) * mm_px
    hi = max(f[4] for f in FORMATS) * mm_px
    ws = np.arange(int(lo), int(min(hi, w - 1)) + 1)
    hs = np.arange(int(SHORT_MM[0] * mm_px), int(min(SHORT_MM[1] * mm_px, h - 1)) + 1)
    return ws, hs


def _pair_curve(lo_e, hi_e, sizes):
    """Je Groesse s: staerkstes Kantenpaar max_x lo[x] * hi[x + s] (beide Kanten noetig)."""
    n = len(lo_e)
    return np.array([np.max(lo_e[:n - s] * hi_e[s:]) if 0 < s < n else 0.0 for s in sizes], np.float32)


def _curves(ev, ws, hs):
    return {"ws": ws, "hs": hs, "cw": _pair_curve(ev["xr"], ev["xf"], ws), "ch": _pair_curve(ev["yr"], ev["yf"], hs)}


def measure(item):
    """Erster Durchlauf fuer ein Bild: Kantenevidenz aus der Bildmitte und ihre Paar-Kurven.
    item = (path, pitch_frac oder None, invert)."""
    path, pitch_frac, invert = item
    gray, tr, scale, size = load(path, invert)
    h, w = gray.shape
    lo, hi = CENTER_BAND
    out = {"path": path, "tr": tr, "scale": scale, "size": size, "h": h, "w": w, "invert": invert}
    out.update(_both_axes(gray, (h * lo, h * hi), (w * lo, w * hi)))
    out.update(_curves(out, *_size_ranges(w, h, pitch_frac * w / PITCH_MM if pitch_frac else None)))
    return out


def remeasure(item):
    """Zweiter Durchlauf: Kantenevidenz ueber die volle Laenge der Kanten des vorlaeufigen Rahmens, Paar-Kurven
    um die vorlaeufige Rollengroesse. item = (path, x0, x1, y0, y1, W, H, invert)."""
    path, x0, x1, y0, y1, W, H, invert = item
    gray = load(path, invert)[0]
    h, w = gray.shape
    m = EDGE_MARGIN
    out = _both_axes(gray, (y0 + m, y1 - m), (x0 + m, x1 - m))
    out.update(_curves(out, np.arange(W - FINE_REACH, min(W + FINE_REACH, w - 1) + 1),
                       np.arange(H - FINE_REACH, min(H + FINE_REACH, h - 1) + 1)))
    return out


ROLL_KERNEL = np.bartlett(4 * STEP_HALF + 3)
ROLL_KERNEL /= ROLL_KERNEL.sum()


def _roll_curve(items, key):
    acc = np.sum([it[key] for it in items], axis=0) / len(items)
    # Um die wahre Groesse ist die Kurve so breit gleich hoch wie die Evidenz einer klaren Kante; das Dreieck legt
    # das Maximum in die Mitte dieser Breite statt an ihren Anfang
    return np.convolve(acc, ROLL_KERNEL, mode="same")


def roll_size(items, mm_px, only=None):
    """Gemeinsame Rahmengroesse der Rolle: Maximum der aufsummierten Kantenpaar-Evidenz beider Achsen unter der
    Nebenbedingung Seitenverhaeltnis im Formatfenster (und, mit Massstab, Groesse im mm-Fenster).

    only: Formatname, wenn das Format schon feststeht (Feinsuche).
    -> {"W", "H", "score_w", "score_h", "format"} oder None."""
    ws, hs = items[0]["ws"], items[0]["hs"]
    if min(len(ws), len(hs)) < len(ROLL_KERNEL):    # der Massstab laesst (fast) keinen Rahmen zu, der in die Datei passt
        return None
    cw, ch = _roll_curve(items, "cw"), _roll_curve(items, "ch")

    best = {}
    for name, a0, a1, mm0, mm1 in FORMATS:
        if only and name != only:
            continue
        w_ok = np.ones(len(ws), bool)
        h_val = ch.copy()
        prior = mm_px and name == "3:2"
        if mm_px:
            w_ok = (ws >= mm0 * mm_px) & (ws <= mm1 * mm_px)
        if prior:
            h_val = h_val - PRIOR_WEIGHT * ((hs / mm_px - GATE_MM[1]) / GATE_TOL_MM[1]) ** 2

        top = None
        for i in np.nonzero(w_ok)[0]:
            ok = (ws[i] / hs >= a0) & (ws[i] / hs <= a1)
            if not ok.any():
                continue
            j = int(np.argmax(np.where(ok, h_val, -9.0)))
            total = cw[i] + h_val[j]
            if prior:
                total -= PRIOR_WEIGHT * ((ws[i] / mm_px - GATE_MM[0]) / GATE_TOL_MM[0]) ** 2
            if top is None or total > top[0]:
                top = (float(total), {"W": int(ws[i]), "H": int(hs[j]), "score_w": float(cw[i]),
                                      "score_h": float(ch[j]), "format": name})
        if top:
            best[name] = top

    if not best:
        return None
    pick = best.get("3:2") or best["square"]
    square = best.get("square")
    if square and pick is not square and square[0] > pick[0] * SQUARE_FACTOR + SQUARE_EXTRA:
        pick = square
    return pick[1]


def best_pos(lo_e, hi_e, size, free=FREE_REACH):
    """Lage der vorderen Kante bei Rahmengroesse ``size``: argmax lo + hi.

    Bis +/- SIZE_SLACK ist die Groesse frei. Darueber hinaus (bis +/- free * size) darf nur ein Paar abweichen,
    dessen beide Kanten klar zu sehen sind, und zahlt je px FREE_COST: Rollen enthalten einzelne Bilder in anderem
    Massstab, ein dunkler Rand soll die Groesse aber nicht verschieben. -> (wert, lage, groesse)"""
    n = len(lo_e)
    reach = max(int(round(free * size)), SIZE_SLACK)
    reach += reach % 2          # Schrittweite 2: die Rollengroesse selbst gehoert zu den Kandidaten
    best = (-9.0, 0, size)
    for ds in range(-reach, reach + 1, 2):
        s = size + ds
        if s >= n or s < 10:
            continue
        v = lo_e[:n - s] + hi_e[s:]
        if abs(ds) > SIZE_SLACK:
            v = np.where(np.minimum(lo_e[:n - s], hi_e[s:]) >= FREE_MIN, v, -1.0)
        i = int(np.argmax(v))
        val = float(v[i]) - FREE_COST * max(0, abs(ds) - SIZE_SLACK)
        if val > best[0] + 1e-6:
            best = (val, i, s)
    return best


def _roll_anchor(items, pos_key, lo, hi):
    """Uebliche Lage des Rahmens in der Datei (Median der Bilder, deren beide Kanten gesehen wurden) oder None."""
    seen = [it[pos_key] for it in items if min(it["ev"][lo], it["ev"][hi]) >= STRONG]
    return float(np.median(seen)) if len(seen) >= ROLL_MIN_N else None


def _anchored(it, lo_key, hi_key, anchor, size, extent):
    """Lage aus der Rolle, wenn keine Kante der Achse traegt. Um 180 Grad gedrehte Dateien liegen gespiegelt;
    es gilt die Lage mit der besseren Evidenz."""
    def clamp(p):
        return max(0, min(extent - 1 - size, int(round(p))))
    cands = [clamp(anchor), clamp(extent - anchor - size)]
    return max(cands, key=lambda p: it[lo_key][p] + it[hi_key][p + size])


def _refine(sharp, pos, flat):
    """Kante auf den steilsten Punkt in ihrer Naehe legen; eine nicht gesehene Kante oder eine am Dateirand bleibt."""
    n = len(sharp)
    if pos <= 0 or pos >= n - 1 or flat[pos] < WEAK:
        return pos
    lo = max(1, pos - REFINE_REACH)
    return lo + int(np.argmax(sharp[lo:min(n - 1, pos + REFINE_REACH + 1)]))


def _seen_size(items, size_key, lo, hi, fallback):
    """Median der Rahmengroesse ueber die Bilder, deren beide Kanten der Achse gesehen wurden."""
    seen = [it[size_key] for it in items if min(it["ev"][lo], it["ev"][hi]) >= STRONG]
    seen = [v for v in seen if abs(v - fallback) <= SIZE_SLACK + 2 * REFINE_REACH]    # ohne Bilder in anderem Massstab
    return int(round(float(np.median(seen)))) if len(seen) >= ROLL_MIN_N else fallback


def _from_seen_edge(it, pos_key, size_key, lo, hi, size, extent):
    """Ist genau eine Kante der Achse gesehen, liegt die andere um die Rollengroesse daneben."""
    e_lo, e_hi = it["ev"][lo], it["ev"][hi]
    if min(e_lo, e_hi) >= WEAK or max(e_lo, e_hi) < STRONG or pos_key[0] in it["from_roll"]:
        return
    far = it[pos_key] + it[size_key]
    start = max(0, far - size) if e_hi > e_lo else it[pos_key]
    it[pos_key] = start
    it[size_key] = min(size, extent - 1 - start)


def _solve(it, W, H):
    _, x0, ws = best_pos(it["xr"], it["xf"], W)
    _, y0, hs = best_pos(it["yr"], it["yf"], H)
    it.update(x0=x0, ws=ws, y0=y0, hs=hs)
    it["ev"] = [float(it["xr"][x0]), float(it["xf"][x0 + ws]), float(it["yr"][y0]), float(it["yf"][y0 + hs])]


def _result(it):
    """Rahmen in Datei-Pixeln, Evidenz in Datei-Richtung (links, oben, rechts, unten)."""
    w, h = it["w"], it["h"]
    x0, y0 = it["x0"], it["y0"]
    x1 = min(x0 + it["ws"] + (1 if x0 + it["ws"] >= w - 1 else 0), w)
    y1 = min(y0 + it["hs"] + (1 if y0 + it["hs"] >= h - 1 else 0), h)
    el, er, et, eb = it["ev"]
    box, ev = [x0, y0, x1 - x0, y1 - y0], [el, et, er, eb]
    if it["tr"]:
        box, ev = [y0, x0, y1 - y0, x1 - x0], [et, el, eb, er]
    s = it["scale"]
    fw, fh = it["size"]
    bx, by = int(round(box[0] * s)), int(round(box[1] * s))
    return {"path": it["path"], "x": bx, "y": by,
            "width": min(int(round(box[2] * s)), fw - bx), "height": min(int(round(box[3] * s)), fh - by),
            "img_w": fw, "img_h": fh, "edges": [round(v, 3) for v in ev],
            "from_roll": it["from_roll"], "size_dev": [it["ws"] - it["W"], it["hs"] - it["H"]],
            "tilt_deg": -it["tilt"] if it["tr"] else it["tilt"]}


def _finish_roll(items, mm_px):
    """Zweite Haelfte fuer eine Rolle: Groesse fein, Lage je Bild, Rueckgriff auf die Rolle. -> (ergebnisse, info)"""
    roll = roll_size(items, mm_px, only=items[0]["roll"]["format"]) or items[0]["roll"]
    W, H = roll["W"], roll["H"]
    for it in items:
        _solve(it, W, H)
        it.update(W=W, H=H, from_roll=[])

    x_anchor = _roll_anchor(items, "x0", 0, 1)
    y_anchor = _roll_anchor(items, "y0", 2, 3)
    for it in items:
        el, er, et, eb = it["ev"]
        if x_anchor is not None and max(el, er) < WEAK:
            it.update(x0=_anchored(it, "xr", "xf", x_anchor, W, it["w"]), ws=W)
            it["from_roll"].append("x")
        if y_anchor is not None and max(et, eb) < WEAK:
            it.update(y0=_anchored(it, "yr", "yf", y_anchor, H, it["h"]), hs=H)
            it["from_roll"].append("y")
        x0, y0 = it["x0"], it["y0"]
        it["ev"] = [float(it["xr"][x0]), float(it["xf"][x0 + it["ws"]]),
                    float(it["yr"][y0]), float(it["yf"][y0 + it["hs"]])]
        x1 = _refine(it["xfs"], x0 + it["ws"], it["xf"])
        y1 = _refine(it["yfs"], y0 + it["hs"], it["yf"])
        x0, y0 = _refine(it["xrs"], x0, it["xr"]), _refine(it["yrs"], y0, it["yr"])
        it.update(x0=x0, ws=x1 - x0, y0=y0, hs=y1 - y0)

    # Rollengroesse aus den Bildern, deren beide Kanten gesehen wurden; eine ungesehene Kante liegt um genau diese
    # Groesse von der gesehenen entfernt
    W = roll["W"] = _seen_size(items, "ws", 0, 1, W)
    H = roll["H"] = _seen_size(items, "hs", 2, 3, H)
    for it in items:
        _from_seen_edge(it, "x0", "ws", 0, 1, W, it["w"])
        _from_seen_edge(it, "y0", "hs", 2, 3, H, it["h"])
        it.update(W=W, H=H)

    scale = items[0]["scale"]
    info = dict(roll, n=len(items), long_px=W * scale, short_px=H * scale,
                mm_px=mm_px / scale if mm_px else None,
                long_mm=W / mm_px if mm_px else None, short_mm=H / mm_px if mm_px else None)
    return [_result(it) for it in items], info


def _sample_score(items, pitch):
    """Kantenevidenz einer Stichprobe: Summe beider Achsen der groessten Gruppe gleicher Arbeitsgroesse."""
    shapes = {}
    for it in items:
        shapes.setdefault((it["w"], it["h"]), []).append(it)
    if not shapes:
        return 0.0
    (w, _), group = max(shapes.items(), key=lambda kv: len(kv[1]))
    roll = roll_size(group, pitch * w / PITCH_MM if pitch else None)
    return roll["score_w"] + roll["score_h"] if roll else 0.0


def detect(rolls, pool_map=map, progress=lambda: None):
    """Rahmen aller Bilder mehrerer Rollen.

    rolls: {name: (pfade, pitch_frac)}; pitch_frac = Perforationstakt relativ zur langen Bildkante (film_scale), wenn
    er als Massstab gilt, sonst None. pool_map(fn, items): verteilt die Arbeit je Bild (Standard: nacheinander).
    progress(): wird je Bild genau zweimal gerufen, nach jedem der zwei Durchlaeufe.
    -> {name: (ergebnisse je Bild, rolleninfo)}; Rollen ohne lesbares Bild oder ohne Loesung fehlen.

    Bilder einer Rolle mit anderer Arbeitsgroesse (anderer Export) bilden eine eigene Gruppe mit eigener
    Rahmengroesse; die Rolleninfo stammt von der groessten Gruppe."""
    # Polung je Rolle: beide an einer Stichprobe messen, die mit der staerkeren Kantenevidenz gilt
    sample = [(name, (p, pitch, inv)) for name, (paths, pitch) in rolls.items()
              for p in paths[::max(1, len(paths) // POLARITY_SAMPLE)][:POLARITY_SAMPLE] for inv in (False, True)]
    measured = {}
    for (name, job), it in zip(sample, pool_map(_measure_safe, [j[1] for j in sample])):
        if it:
            measured[(job[0], job[2])] = it
    invert = {}
    for name, (paths, pitch) in rolls.items():
        score = {inv: _sample_score([measured[(p, inv)] for p in paths if (p, inv) in measured], pitch)
                 for inv in (False, True)}
        invert[name] = score[True] >= POLARITY_MIN and score[True] > POLARITY_LEAD * score[False]

    jobs = [(name, (p, pitch, invert[name])) for name, (paths, pitch) in rolls.items() for p in paths]
    todo = [j for j in jobs if (j[1][0], j[1][2]) not in measured]      # die Stichprobe ist schon gemessen
    for (name, job), it in zip(todo, pool_map(_measure_safe, [j[1] for j in todo])):
        if it:
            measured[(job[0], job[2])] = it
    groups = {}             # (rolle, arbeitsgroesse) -> bilder: gemeinsam gemessen wird nur bei gleichem Raster
    for name, job in jobs:
        progress()
        it = measured.get((job[0], job[2]))
        if it:
            groups.setdefault((name, it["w"], it["h"]), []).append(it)

    second, solved = [], {}
    for key, items in groups.items():
        pitch = rolls[key[0]][1]
        mm_px = pitch * key[1] / PITCH_MM if pitch else None
        roll = roll_size(items, mm_px)
        if roll is None:
            continue
        solved[key] = (items, mm_px)
        for it in items:
            _, x0, ws = best_pos(it["xr"], it["xf"], roll["W"], free=0)
            _, y0, hs = best_pos(it["yr"], it["yf"], roll["H"], free=0)
            it["roll"] = roll
            second.append((it, (it["path"], x0, x0 + ws, y0, y0 + hs, roll["W"], roll["H"], it["invert"])))

    for (it, _), ev in zip(second, pool_map(remeasure, [s[1] for s in second])):
        it.update(ev)
        progress()

    out = {}
    for name, (paths, _) in rolls.items():
        parts = [_finish_roll(*solved[key]) for key in solved if key[0] == name]
        if not parts:
            continue
        order = {p: i for i, p in enumerate(paths)}
        res = sorted((r for part, _ in parts for r in part), key=lambda r: order[r["path"]])
        out[name] = (res, max(parts, key=lambda part: part[1]["n"])[1])     # Rolleninfo der groessten Gruppe
    return out


def _measure_safe(item):
    try:
        return measure(item)
    except Exception:      # noqa: BLE001 - ein unlesbares Bild darf die Rolle nicht kippen
        return None

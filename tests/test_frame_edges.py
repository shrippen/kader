"""Tests der Rahmenkanten-Erkennung je Rolle (frame_edges.py) und ihres Wegs durch kader.compute_batch.

Gezeichnete Scans: heller Halter, dunkler Filmstreifen, heller Rahmen mit Rauschen als Bildinhalt. Jedes Bild einer
Rolle liegt anders, das Bildfenster ist immer gleich gross.

Ausfuehren:  .venv/bin/python -m unittest tests.test_frame_edges -v
"""
import os
import shutil
import sys
import tempfile
import unittest
import unittest.mock

import cv2
import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

import frame_edges as fe  # noqa: E402
import kader              # noqa: E402

IMG_W, IMG_H = 1500, 1000
MM_PX = 34.8                               # Abbildungsmassstab der gezeichneten Scans
PITCH_FRAC = fe.PITCH_MM * MM_PX / IMG_W   # Perforationstakt relativ zur langen Kante
FRAME_W, FRAME_H = 1274, 849               # 36,6 x 24,4 mm
SQUARE_W = 867                             # 24,9 mm
REBATE, HOLDER = 18, 235                   # Grauwert Filmrand, Halter
OFFSETS = ((90, 70), (120, 76), (104, 73), (133, 71), (97, 78), (111, 74))   # (x, y) des Rahmens je Bild
TOL_PX = 3
CUT_ROWS = 10                              # so viele Zeilen fehlen einem Bild anderer Groesse


def scan(x0, y0, seed, frame_w=FRAME_W, dark_left=0.0, black=False, strip=(8, IMG_H - 8)):
    """Ein Scan: Rahmen (x0, y0, frame_w x FRAME_H) im Filmstreifen. dark_left: Anteil der Rahmenbreite links, der
    so dunkel wie der Filmrand ist (Schatten im Motiv); black: ganzer Rahmen ohne Zeichnung."""
    rng = np.random.default_rng(seed)
    g = np.full((IMG_H, IMG_W), float(HOLDER))
    g[strip[0]:strip[1], :] = REBATE
    if not black:
        content = 150 + 50 * rng.random((FRAME_H // 40 + 1, frame_w // 40 + 1))
        content = cv2.resize(content, (frame_w, FRAME_H), interpolation=cv2.INTER_CUBIC)
        y1, x1 = min(y0 + FRAME_H, IMG_H), min(x0 + frame_w, IMG_W)
        g[max(y0, 0):y1, x0:x1] = content[max(-y0, 0):y1 - y0, :x1 - x0]
        g[max(y0, 0):y1, x0:x0 + int(dark_left * frame_w)] = REBATE
    g += rng.normal(0, 1.5, g.shape)
    return np.clip(g, 0, 255).astype(np.uint8)


class _Rolls(unittest.TestCase):
    """Gemeinsames Werkzeug: Scans in einen Rollenordner schreiben, Rahmen vergleichen."""

    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.tmp, True)

    def write(self, images, roll="Rolle"):
        os.makedirs(os.path.join(self.tmp, roll), exist_ok=True)
        paths = []
        for i, g in enumerate(images):
            paths.append(os.path.join(self.tmp, roll, f"{i:02d}.png"))
            cv2.imwrite(paths[-1], g)
        return paths

    def detect(self, images, pitch=PITCH_FRAC):
        paths = self.write(images)
        return fe.detect({"Rolle": (paths, pitch)})["Rolle"]

    def assertBox(self, res, x, y, w, h, tol=TOL_PX):
        for name, want in (("x", x), ("y", y), ("width", w), ("height", h)):
            self.assertAlmostEqual(res[name], want, delta=tol, msg=f"{name}: {res}")


class RollTest(_Rolls):
    def test_finds_frame_of_every_picture(self):
        res, info = self.detect([scan(x, y, i) for i, (x, y) in enumerate(OFFSETS)])
        self.assertEqual(info["format"], "3:2")
        self.assertAlmostEqual(info["W"], FRAME_W, delta=TOL_PX)
        self.assertAlmostEqual(info["H"], FRAME_H, delta=TOL_PX)
        self.assertAlmostEqual(info["long_mm"], 36.6, delta=0.1)
        for r, (x, y) in zip(res, OFFSETS):
            self.assertBox(r, x, y, FRAME_W, FRAME_H)
            self.assertGreater(min(r["edges"]), 0.8)

    def test_unseen_edge_comes_from_roll_size(self):
        # das linke Viertel des Motivs ist so dunkel wie der Filmrand: die rechte Kante und die Rollengroesse tragen
        images = [scan(x, y, i) for i, (x, y) in enumerate(OFFSETS)]
        images[2] = scan(*OFFSETS[2], seed=2, dark_left=0.25)
        res, _ = self.detect(images)
        self.assertBox(res[2], *OFFSETS[2], FRAME_W, FRAME_H)
        left, top, right, bottom = res[2]["edges"]
        self.assertLess(left, fe.WEAK)                       # nicht gesehen, also keine Sicherheit
        self.assertGreater(min(top, right, bottom), 0.6)

    def test_black_frame_takes_position_from_roll(self):
        images = [scan(x, y, i) for i, (x, y) in enumerate(OFFSETS)]
        images[4] = scan(*OFFSETS[4], seed=4, black=True)
        res, _ = self.detect(images)
        self.assertEqual(res[4]["from_roll"], ["x", "y"])
        xs, ys = sorted(o[0] for o in OFFSETS), sorted(o[1] for o in OFFSETS)
        self.assertBox(res[4], xs[len(xs) // 2], ys[len(ys) // 2], FRAME_W, FRAME_H, tol=12)
        self.assertLess(min(res[4]["edges"]), fe.WEAK)

    def test_square_frames_on_35mm(self):
        res, info = self.detect([scan(x + 150, y, i, frame_w=SQUARE_W) for i, (x, y) in enumerate(OFFSETS)])
        self.assertEqual(info["format"], "square")
        for r, (x, y) in zip(res, OFFSETS):
            self.assertBox(r, x + 150, y, SQUARE_W, FRAME_H)

    def test_single_picture_in_other_scale_keeps_its_own_edges(self):
        # ein Bild der Rolle ist 3 % kleiner abgebildet: beide Kanten klar zu sehen, also gilt, was zu sehen ist
        images = [scan(x, y, i) for i, (x, y) in enumerate(OFFSETS)]
        small = FRAME_W - 38
        images[1] = scan(*OFFSETS[1], seed=1, frame_w=small)
        res, info = self.detect(images)
        self.assertAlmostEqual(info["W"], FRAME_W, delta=TOL_PX)
        self.assertBox(res[1], *OFFSETS[1], small, FRAME_H)

    def test_frame_running_past_the_file_ends_at_the_border(self):
        # Scan ohne Perforation, Rahmen oben und unten angeschnitten: der Crop endet am Dateirand
        images = [scan(x, -12, i, strip=(0, IMG_H)) for i, (x, _) in enumerate(OFFSETS)]
        res, info = self.detect(images, pitch=None)
        self.assertIsNone(info["mm_px"])
        for r, (x, _) in zip(res, OFFSETS):
            self.assertEqual(r["y"], 0)
            self.assertAlmostEqual(r["height"], FRAME_H - 12, delta=TOL_PX)
            self.assertAlmostEqual(r["x"], x, delta=TOL_PX)
            self.assertLessEqual(r["edges"][1], fe.BORDER_EVIDENCE + 0.01)    # oben nichts gesehen

    def test_tilted_frame_keeps_its_evidence(self):
        # 0,6 Grad Schraeglage: die Kante laeuft ueber ihre Laenge 13 px weit
        rot = cv2.getRotationMatrix2D((IMG_W / 2, IMG_H / 2), 0.6, 1.0)
        images = [cv2.warpAffine(scan(x, y, i), rot, (IMG_W, IMG_H), borderValue=HOLDER)
                  for i, (x, y) in enumerate(OFFSETS)]
        res, _ = self.detect(images)
        for r in res:
            self.assertGreater(min(r["edges"]), 0.7, r)
            self.assertAlmostEqual(abs(r["tilt_deg"]), 0.6, delta=0.21)

    def test_portrait_file_reports_edges_in_file_orientation(self):
        # Hochkant-Datei (um 90 Grad im Uhrzeigersinn gedreht): die linke Kante des Rahmens liegt in der Datei oben
        images = [np.ascontiguousarray(np.rot90(scan(x, y, i, dark_left=0.25 if i == 0 else 0.0), k=-1))
                  for i, (x, y) in enumerate(OFFSETS)]
        res, _ = self.detect(images)
        x, y = OFFSETS[0]
        self.assertBox(res[0], IMG_H - y - FRAME_H, x, FRAME_H, FRAME_W)
        self.assertEqual(min(range(4), key=lambda i: res[0]["edges"][i]), 1)       # links, oben, rechts, unten
        self.assertEqual((res[0]["img_w"], res[0]["img_h"]), (IMG_H, IMG_W))

    def test_axis_from_roll_is_named_in_file_orientation(self):
        # linkes und rechtes Fuenftel des Rahmens so dunkel wie der Filmrand: links/rechts kommt aus der Rolle
        def dark_sides(i, x, y):
            g = scan(x, y, i)
            band = FRAME_W // 5
            g[y:y + FRAME_H, x:x + band] = REBATE
            g[y:y + FRAME_H, x + FRAME_W - band:x + FRAME_W] = REBATE
            return g
        images = [dark_sides(i, x, y) if i == 2 else scan(x, y, i) for i, (x, y) in enumerate(OFFSETS)]
        self.assertEqual(self.detect(images)[0][2]["from_roll"], ["x"])
        portrait = [np.ascontiguousarray(np.rot90(g, k=-1)) for g in images]
        self.assertEqual(self.detect(portrait)[0][2]["from_roll"], ["y"])     # in der Datei oben und unten

    def test_picture_of_another_size_keeps_its_result(self):
        # ein Export mit anderer Hoehe (etwa nach einer Drehung im RAW-Entwickler) darf die Rolle nicht kippen
        images = [scan(x, y, i) for i, (x, y) in enumerate(OFFSETS)]
        images[0] = images[0][:IMG_H - CUT_ROWS]
        res, info = self.detect(images)
        self.assertEqual(len(res), len(OFFSETS))
        self.assertEqual(info["n"], len(OFFSETS) - 1)
        for r, (x, y) in zip(res, OFFSETS):
            self.assertBox(r, x, y, FRAME_W, FRAME_H)

    def test_roll_not_inverted_is_found_too(self):
        # nicht invertierte Negative: Filmrand hell, Bild dunkler
        res, _ = self.detect([255 - scan(x, y, i) for i, (x, y) in enumerate(OFFSETS)])
        for r, (x, y) in zip(res, OFFSETS):
            self.assertBox(r, x, y, FRAME_W, FRAME_H)

    def test_roll_with_impossible_scale_does_not_stop_the_others(self):
        # Takt doppelt so gross wie wahr: kein Rahmen passt mehr in die Datei
        good = self.write([scan(x, y, i) for i, (x, y) in enumerate(OFFSETS)], "gut")
        bad = self.write([scan(x, y, i) for i, (x, y) in enumerate(OFFSETS)], "falsch")
        found = fe.detect({"gut": (good, PITCH_FRAC), "falsch": (bad, 2 * PITCH_FRAC)})
        self.assertEqual(sorted(found), ["gut"])
        self.assertBox(found["gut"][0][0], *OFFSETS[0], FRAME_W, FRAME_H)

    def test_roll_with_barely_fitting_scale_does_not_stop_the_others(self):
        # Takt 1,22-fach: nur noch eine Handvoll Rahmengroessen passen in die Datei
        good = self.write([scan(x, y, i) for i, (x, y) in enumerate(OFFSETS)], "gut")
        bad = self.write([scan(x, y, i) for i, (x, y) in enumerate(OFFSETS)], "falsch")
        found = fe.detect({"gut": (good, PITCH_FRAC), "falsch": (bad, 1.22 * PITCH_FRAC)})
        self.assertEqual(sorted(found), ["gut"])

    def test_progress_follows_the_measurements(self):
        # mehr Bilder als die Stichprobe zur Polung, dazu eine unlesbare Datei: jedes zaehlt zwei Schritte
        offsets = OFFSETS + OFFSETS[:4]
        paths = self.write([scan(x, y, i) for i, (x, y) in enumerate(offsets)])
        self.assertGreater(len(paths), fe.POLARITY_SAMPLE)
        broken = os.path.join(self.tmp, "Rolle", "kaputt.png")
        with open(broken, "w") as f:
            f.write("kein Bild")
        events = []

        def pool_map(fn, items):
            for it in items:
                events.append("ergebnis")
                yield fn(it)
        fe.detect({"Rolle": (paths + [broken], PITCH_FRAC)}, pool_map, lambda: events.append("schritt"))
        self.assertEqual(events.count("schritt"), 2 * (len(paths) + 1))
        self.assertLess(events.index("schritt"), 3)         # nicht erst, wenn alle gemessen sind

    def test_unreadable_file_does_not_stop_the_roll(self):
        paths = self.write([scan(x, y, i) for i, (x, y) in enumerate(OFFSETS)])
        broken = os.path.join(self.tmp, "Rolle", "kaputt.png")
        with open(broken, "w") as f:
            f.write("kein Bild")
        res, _ = fe.detect({"Rolle": (paths + [broken], PITCH_FRAC)})["Rolle"]
        self.assertEqual([r["path"] for r in res], paths)


class BatchTest(_Rolls):
    """Der Weg durch kader.compute_batch: Ausgabeformat, Abstand zur Kante, Rueckfall."""

    def batch(self, images, fmt="35mm"):
        paths = self.write(images)
        scales = unittest.mock.patch.object(
            kader, "_scale_worker", _FixedScale(PITCH_FRAC))
        with scales:
            out = kader.compute_batch(paths, 0.3, False, fmt, report=lambda msg: None)
        return {os.path.basename(r["input_file"]): r for r in out["results"]}, out

    def test_batch_uses_frame_edges(self):
        by, out = self.batch([scan(x, y, i) for i, (x, y) in enumerate(OFFSETS)])
        self.assertEqual(out["film_aspects"]["Rolle"]["source"], "edges")
        inset = kader.EDGES_INSET * FRAME_W
        for i, (x, y) in enumerate(OFFSETS):
            r = by[f"{i:02d}.png"]
            self.assertEqual(r["method"], "frame_edges")
            self.assertBox(r, x + inset, y + inset, FRAME_W - 2 * inset, FRAME_H - 2 * inset)
            self.assertEqual(sorted(r["_conf_parts"]), sorted(kader.EDGE_PARTS))
            self.assertAlmostEqual(r["confidence"], min(r["_conf_parts"].values()), delta=0.001)
            self.assertFalse(r["needs_review"])
            self.assertEqual((r["_img_w"], r["_img_h"]), (IMG_W, IMG_H))

    def test_other_format_runs_candidate_strategies(self):
        by, _ = self.batch([scan(x, y, i) for i, (x, y) in enumerate(OFFSETS)], fmt="6x6")
        self.assertTrue(by)
        for r in by.values():
            self.assertNotEqual(r["method"], "frame_edges")

    def test_progress_ends_at_total(self):
        paths = self.write([scan(x, y, i) for i, (x, y) in enumerate(OFFSETS)])
        seen = []
        with unittest.mock.patch.object(kader, "_scale_worker", _FixedScale(PITCH_FRAC)):
            kader.compute_batch(paths, 0.3, False, "35mm", report=seen.append)
        ticks = [m.split()[1] for m in seen if m.startswith("PROGRESS")]
        self.assertEqual(ticks[-1], f"{2 * len(paths)}/{2 * len(paths)}")
        self.assertEqual(len(ticks), 2 * len(paths))


class _FixedScale:
    """Ersetzt die Takt-Messung: die gezeichneten Scans haben keine Perforation. Als Klasse auf Modulebene, damit
    der Prozesspool sie uebergeben kann."""

    def __init__(self, pitch_frac):
        self.pitch_frac = pitch_frac

    def __call__(self, item):
        return item[0], {"pitch": self.pitch_frac * IMG_W, "pitch_frac": self.pitch_frac, "score": 0.9,
                         "agree": 0.001, "n": len(item[1])}


if __name__ == "__main__":
    unittest.main()

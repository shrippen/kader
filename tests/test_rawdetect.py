"""Tests des Erkennungsbilds aus dem RAW (companion/rawdetect.py) und seines Wegs durch die Analyse.

Ohne echte RAWs: das lineare Sensorbild wird gezeichnet. Dia: Filmrand fast schwarz, Bild knapp darueber.
Negativ: Filmrand hell, Bild dunkler.

Ausfuehren:  .venv/bin/python -m unittest tests.test_rawdetect -v
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

from companion import rawdetect as rd          # noqa: E402
from companion import session as sess          # noqa: E402
from companion.detect import Analyzer          # noqa: E402
from companion.sources import standalone_job   # noqa: E402
from tests import test_frame_edges as scans    # noqa: E402

W, H = scans.IMG_W, scans.IMG_H
FRAME = (104, 73, scans.FRAME_W, scans.FRAME_H)
EXPORT_GAIN = 0.04          # der Export ist fast schwarz: 0..9 von 255
EXPORT_SCALE = 2            # der Export ist groesser als das Erkennungsbild
EDGE_STEP = 20              # so viele Grauwerte trennt das Erkennungsbild Filmrand und Bild mindestens
TOL = 0.004                 # Anteil der Bildkante
CUT_ROWS = 12               # Zeilen, die einem gedrehten Export fehlen (1,2 % der Hoehe)


def slide(g):
    """Lineares Sensorbild eines Dias: Filmrand bei Dichte 3, das Bild bis eine halbe Stufe darueber."""
    return (10.0 ** (-3.0 + 0.5 * g / 255.0)).astype(np.float32)


def negative(g):
    """Lineares Sensorbild eines Negativs: Filmrand hell, Bild dunkler."""
    return (0.6 * 10.0 ** (-0.5 * g / 255.0)).astype(np.float32)


def export_of(g):
    big = cv2.resize(g, (W * EXPORT_SCALE, H * EXPORT_SCALE), interpolation=cv2.INTER_LINEAR)
    return (big * EXPORT_GAIN).astype(np.uint8)


def inside_outside(img):
    """Mittlerer Grauwert knapp innerhalb und knapp ausserhalb der linken Rahmenkante."""
    x, y, _, h = FRAME
    rows = slice(y + 50, y + h - 50)
    return float(img[rows, x + 5:x + 25].mean()), float(img[rows, x - 25:x - 5].mean())


class StretchTest(unittest.TestCase):
    def setUp(self):
        self.g = scans.scan(FRAME[0], FRAME[1], seed=1)

    def test_export_hides_the_edge_and_density_image_shows_it(self):
        inner, outer = inside_outside(export_of(self.g)[::EXPORT_SCALE, ::EXPORT_SCALE])
        self.assertLess(inner - outer, EDGE_STEP)
        inner, outer = inside_outside(rd.stretch(slide(self.g), rd.POS))
        self.assertGreater(inner - outer, EDGE_STEP)

    def test_negative_gets_dark_border_and_brighter_picture(self):
        inner, outer = inside_outside(rd.stretch(negative(self.g), rd.NEG))
        self.assertGreater(inner - outer, EDGE_STEP)


class OrientTest(unittest.TestCase):
    def setUp(self):
        self.lin = slide(scans.scan(FRAME[0], FRAME[1], seed=2))

    def test_takes_rotation_and_mirror_from_an_inverted_export(self):
        turned = np.rot90(self.lin[:, ::-1], 1)                     # gespiegelt und gedreht
        export = 255 - (255 * np.sqrt(turned / turned.max())).astype(np.uint8)
        got = rd.orient(self.lin, export)
        self.assertEqual(got.shape, export.shape)
        self.assertGreater(np.corrcoef(got.ravel(), turned.ravel())[0, 1], 0.99)

    def test_shrinks_to_working_size_of_the_export(self):
        export = cv2.resize(self.lin, (3 * W, 3 * H))
        self.assertEqual(max(rd.orient(self.lin, (export * 2e4).clip(0, 255).astype(np.uint8)).shape), rd.LONG)

    def test_export_with_another_cutout_gives_no_image(self):
        # im RAW-Entwickler gedreht: der Export ist ein kleinerer Ausschnitt mit anderem Seitenverhaeltnis
        export = (255 * np.sqrt(self.lin / self.lin.max())).astype(np.uint8)[:H - CUT_ROWS]
        self.assertIsNone(rd.orient(self.lin, export))

    def test_unrelated_export_gives_no_image(self):
        noise = np.random.default_rng(3).integers(0, 255, (H, W)).astype(np.uint8)
        self.assertIsNone(rd.orient(self.lin, noise))


class RollTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.tmp, True)

    def roll(self, to_linear):
        bases = []
        for i, (x, y) in enumerate(scans.OFFSETS):
            base = os.path.join(self.tmp, f"b{i}")
            lin = to_linear(scans.scan(x, y, seed=i))
            for pol in rd.POLARITIES:
                cv2.imwrite(rd.path_for(base, pol), rd.stretch(lin, pol))
            bases.append(base)
        return bases

    def test_slide_roll_is_positive(self):
        self.assertEqual(rd.polarity(self.roll(slide)), rd.POS)

    def test_negative_roll_is_negative(self):
        self.assertEqual(rd.polarity(self.roll(negative)), rd.NEG)

    def test_settle_keeps_one_polarity_and_reuses_it(self):
        bases = self.roll(slide)
        self.assertEqual(rd.settle(bases), rd.POS)
        self.assertFalse(os.path.exists(rd.path_for(bases[0], rd.NEG)))
        with unittest.mock.patch.object(rd, "polarity", side_effect=AssertionError("neu bestimmt")):
            self.assertEqual(rd.settle(bases), rd.POS)

    def test_roll_with_a_missing_image_has_no_polarity(self):
        bases = self.roll(slide)
        for pol in rd.POLARITIES:
            os.remove(rd.path_for(bases[0], pol))
        self.assertIsNone(rd.settle(bases))


class AnalyzerTest(unittest.TestCase):
    """RAW-Ordner durch die Analyse: gemessen wird auf dem Erkennungsbild, das Ergebnis gilt fuer den Export."""

    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.tmp, True)
        self.linear = {}
        folder = os.path.join(self.tmp, "Scans", "Rolle")
        os.makedirs(folder)
        for i, (x, y) in enumerate(scans.OFFSETS):
            raw = os.path.join(folder, f"a{i}.nef")
            open(raw, "wb").close()
            self.linear[raw] = scans.scan(x, y, seed=i)

    def export_many(self, jobs, on_done, name, workers=4):
        for iid, raw, out in jobs:
            os.makedirs(os.path.dirname(out), exist_ok=True)
            cv2.imwrite(out, export_of(self.linear[raw]))
            on_done(iid, out, None)

    def analyze(self, available=True, fmt=None):
        job = standalone_job(os.path.join(self.tmp, "Scans"), settings={"format": fmt} if fmt else None)
        job.update(target="json", converter="rawpy", out=os.path.join(self.tmp, "out"))
        s = sess.Session.create(job, os.path.join(self.tmp, "root"))
        an = Analyzer(s)
        with unittest.mock.patch("companion.converters.export_many", self.export_many), \
                unittest.mock.patch.object(rd, "linear", lambda raw: slide(self.linear[raw])), \
                unittest.mock.patch.object(rd, "available", return_value=available), \
                unittest.mock.patch("companion.detect._pool_map", lambda fn, items: map(fn, items)):
            an.start_analysis()
            an.wait(300)
        return s, an

    def test_crop_from_density_image_fits_the_export(self):
        s, an = self.analyze()
        self.assertTrue(any("(pos)" in line for line in an.log), list(an.log))
        for img, (x, y) in zip(s.state["images"].values(), scans.OFFSETS):
            self.assertEqual(img["status"], "done", img.get("error"))
            self.assertEqual(img["export_size"], [W * EXPORT_SCALE, H * EXPORT_SCALE])
            det = img["detected"]
            self.assertTrue(any(r["key"] == "raw_image" for r in det["reasons"]), det["reasons"])
            want = [x / W, y / H, (x + scans.FRAME_W) / W, (y + scans.FRAME_H) / H]
            inset = [det["crop"][0] - want[0], det["crop"][1] - want[1], want[2] - det["crop"][2], want[3] - det["crop"][3]]
            for d in inset:                                # der Crop sitzt um den Einzug innerhalb des Rahmens
                self.assertGreaterEqual(d, -TOL, (det["crop"], want))
                self.assertLess(d, 3 * TOL + 0.005, (det["crop"], want))

    def test_picture_with_another_cutout_is_measured_on_the_export(self):
        first = sorted(self.linear)[0]
        real = self.export_many

        def cut(jobs, on_done, name, workers=4):
            real(jobs, on_done, name, workers)
            for _, raw, out in jobs:
                if raw == first:
                    cv2.imwrite(out, cv2.imread(out, cv2.IMREAD_GRAYSCALE)[:(H - CUT_ROWS) * EXPORT_SCALE])
        self.export_many = cut
        s, an = self.analyze()
        imgs = sorted(s.state["images"].values(), key=lambda i: i["path"])
        self.assertEqual([i["status"] for i in imgs], ["done"] * len(imgs))
        on_raw = [any(r["key"] == "raw_image" for r in i["detected"]["reasons"]) for i in imgs]
        self.assertEqual(on_raw, [False] + [True] * (len(imgs) - 1))
        self.assertEqual(imgs[0]["export_size"], [W * EXPORT_SCALE, (H - CUT_ROWS) * EXPORT_SCALE])

    def test_other_format_is_measured_on_the_export(self):
        s, an = self.analyze(fmt="6x6")
        self.assertFalse(os.path.exists(s.path("detect")))
        self.assertFalse(any("RAW" in line for line in an.log), list(an.log))

    def test_without_rawpy_the_export_is_measured(self):
        s, an = self.analyze(available=False)
        self.assertFalse(os.path.exists(s.path("detect")))
        for img in s.state["images"].values():
            self.assertEqual(img["status"], "done", img.get("error"))
            self.assertFalse(any(r["key"] == "raw_image" for r in img["detected"]["reasons"]))


if __name__ == "__main__":
    unittest.main()

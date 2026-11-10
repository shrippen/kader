"""Tests der Schraeglagen-Messung (kader.measure_skew).

Ausfuehren:  .venv/bin/python -m unittest tests.test_skew -v
"""
import math
import os
import sys
import unittest

import cv2
import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

import kader  # noqa: E402

IMG_W, IMG_H = 1400, 933
BOX = (150, 120, 1100, 700)        # x, y, w, h des Rahmens
REBATE, PICTURE = 20, 170
TILT_DEG = 0.5
TOL_DEG = 0.1


def frame(long_deg, short_deg):
    """Rahmen, dessen lange Kanten um long_deg und dessen kurze Kanten um short_deg geneigt sind."""
    x, y, w, h = BOX
    dy = w / 2 * math.tan(math.radians(long_deg))       # lange Kanten: rechts tiefer
    dx = h / 2 * math.tan(math.radians(short_deg))      # kurze Kanten: unten weiter links
    pts = np.array([[x + dx, y - dy], [x + w + dx, y + dy], [x + w - dx, y + h + dy], [x - dx, y + h - dy]])
    img = np.full((IMG_H, IMG_W), REBATE, np.uint8)
    cv2.fillPoly(img, [np.round(pts * 16).astype(np.int32)], PICTURE, lineType=cv2.LINE_AA, shift=4)
    return img


class SkewTest(unittest.TestCase):
    def test_rotated_frame(self):
        sk = kader.measure_skew(frame(TILT_DEG, TILT_DEG), *BOX)
        self.assertAlmostEqual(sk["deg"], TILT_DEG, delta=TOL_DEG)

    def test_one_side_cut_straight_does_not_decide(self):
        img = frame(TILT_DEG, TILT_DEG)
        x, y, w, h = BOX
        img[:, x + w - 12:] = REBATE                    # rechte Kante gerade abgeschnitten: Winkel 0
        sk = kader.measure_skew(img, x, y, w - 12, h)
        self.assertAlmostEqual(sk["deg"], TILT_DEG, delta=TOL_DEG)


if __name__ == "__main__":
    unittest.main()

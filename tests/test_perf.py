"""Laufzeit-Eigenschaften der Erkennung, die still verloren gehen koennten.

- Hough laeuft auf der unterabgetasteten Kantenkarte (HoughLinesP kostete ~90 % von find_best_crop).
- Worker-Prozesse nutzen einen OpenCV-Thread (sonst ueberbuchen N Prozesse x N Threads die Kerne).
"""
import os
import sys
import unittest
import unittest.mock

import cv2
import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

import kader  # noqa: E402

IMG_W, IMG_H = 600, 400
FRAME = (100, 80, 400, 240)     # x, y, w, h des gezeichneten Rahmens
TOL_PX = 3                      # Unterabtastung um 2: hoechstens 1-2 px je Endpunkt


def _frame_edges():
    """Dilatierte Kantenkarte eines Rechtecks, wie in detect_by_canny_hough."""
    edges = np.zeros((IMG_H, IMG_W), np.uint8)
    x, y, w, h = FRAME
    cv2.rectangle(edges, (x, y), (x + w, y + h), 255, 1)
    return cv2.dilate(edges, np.ones((3, 3), np.uint8))


class HoughTest(unittest.TestCase):
    def test_runs_on_subsampled_map(self):
        edges = _frame_edges()
        real = cv2.HoughLinesP
        seen = []

        def spy(img, *a, **kw):
            seen.append(img.shape)
            return real(img, *a, **kw)

        with unittest.mock.patch.object(kader.cv2, "HoughLinesP", spy):
            kader.detect_by_canny_hough(edges)
        self.assertTrue(seen)
        for shape in seen:
            self.assertLessEqual(shape[0] * shape[1], IMG_W * IMG_H // 4)

    def test_lines_in_full_coordinates(self):
        lines = kader._hough_lines(_frame_edges(), IMG_H, IMG_W).reshape(-1, 4)
        x, y, w, h = FRAME
        ys = [(y1 + y2) / 2 for x1, y1, x2, y2 in lines if abs(y2 - y1) < 5]
        xs = [(x1 + x2) / 2 for x1, y1, x2, y2 in lines if abs(x2 - x1) < 5]
        self.assertAlmostEqual(min(ys), y, delta=TOL_PX)
        self.assertAlmostEqual(max(ys), y + h, delta=TOL_PX)
        self.assertAlmostEqual(min(xs), x, delta=TOL_PX)
        self.assertAlmostEqual(max(xs), x + w, delta=TOL_PX)


class PoolTest(unittest.TestCase):
    def test_worker_uses_one_opencv_thread(self):
        with kader._process_pool(1) as ex:
            self.assertEqual(ex.submit(cv2.getNumThreads).result(), 1)


if __name__ == "__main__":
    unittest.main()

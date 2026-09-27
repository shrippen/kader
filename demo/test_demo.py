"""Demo-Rollen (demo/rolls.py, intern): Anzahl, Rollenordner, deterministisch.

Ausfuehren:  .venv/bin/python -m unittest discover -s demo -v
"""
import hashlib
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import rolls as demo                  # noqa: E402
from companion.sources import standalone_job   # noqa: E402


def _digest(folder):
    h = hashlib.sha256()
    for dp, _, files in sorted(os.walk(folder)):
        for f in sorted(files):
            with open(os.path.join(dp, f), "rb") as fh:
                h.update(fh.read())
    return h.hexdigest()


class DemoTest(unittest.TestCase):
    def test_rolls_from_world(self):
        with tempfile.TemporaryDirectory() as a, tempfile.TemporaryDirectory() as b:
            self.assertEqual(demo.generate(a), 22)
            job = standalone_job(a)
            self.assertEqual({i["film"] for i in job["images"]},
                             {"Rolle 03 – Övelgönne", "Rolle 04 – Speiche"})
            demo.generate(b)
            self.assertEqual(_digest(a), _digest(b))


if __name__ == "__main__":
    unittest.main()

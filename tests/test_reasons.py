"""Gruende der Erkennung: Schluessel, die die Web-Oberflaeche in beiden Sprachen kennt.

Die Erkennung liefert jeden Grund als {"key", "args"}; companion/static/i18n.js uebersetzt ihn (reason_<key>,
Begriffe in den Argumenten als term_<name>). Fehlt ein Text, saehe man in der Oberflaeche den nackten Schluessel.

Ausfuehren:  .venv/bin/python -m unittest tests.test_reasons -v
"""
import os
import re
import sys
import unittest

import cv2

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

import kader  # noqa: E402
from tests.test_frame_edges import BatchTest, OFFSETS, _Rolls, scan  # noqa: E402

I18N = os.path.join(ROOT, "companion", "static", "i18n.js")
SOURCES = ("kader.py", os.path.join("companion", "detect.py"))
TEST_JPG = os.path.join(ROOT, "test.jpg")
PLACEHOLDER = re.compile(r"\{(\d+)\}")


def dictionaries():
    """{sprache: {schluessel: text}} aus i18n.js (nur die Eintraege reason_* und term_*)."""
    src = open(I18N, encoding="utf-8").read()
    out = {}
    for lang in ("en", "de"):
        block = src[src.index(f"\n  {lang}: {{"):]
        block = block[:block.index("\n  },")]
        out[lang] = dict(re.findall(r"\b((?:reason|term)_\w+): '((?:[^'\\]|\\.)*)'", block))
    return out


def used_in_source():
    """(reason-Schluessel, term-Namen), die der Code verwendet."""
    reasons, terms = set(), set()
    for rel in SOURCES:
        src = open(os.path.join(ROOT, rel), encoding="utf-8").read()
        reasons |= set(re.findall(r"\breason\(\s*\"(\w+)\"", src))
        terms |= set(re.findall(r"\bterm\(\s*\"(\w+)\"\s*\)", src))     # nur ganze Namen
    from companion.detect import RAW_KINDS
    terms |= {f"side_{s}" for s in kader.EDGE_SIDES} | set(RAW_KINDS.values())     # zusammengesetzte Namen
    return reasons, terms


def check(test, reasons):
    texts = dictionaries()
    for r in reasons:
        test.assertIsInstance(r, dict, r)
        for lang in ("en", "de"):
            text = texts[lang].get("reason_" + r["key"])
            test.assertIsNotNone(text, f"{lang}: reason_{r['key']}")
            want = {int(i) for i in PLACEHOLDER.findall(text)}
            test.assertEqual(want, set(range(len(r["args"]))), f"{lang}: reason_{r['key']} {r['args']}")
        for a in r["args"]:
            if isinstance(a, dict):
                for lang in ("en", "de"):
                    test.assertIn("term_" + a["t"], texts[lang], a)
            else:
                test.assertIsInstance(a, str, r)


class SourceTest(unittest.TestCase):
    def test_every_reason_and_term_has_both_languages(self):
        texts = dictionaries()
        reasons, terms = used_in_source()
        self.assertTrue(reasons)
        for lang in ("en", "de"):
            for key in reasons:
                self.assertIn("reason_" + key, texts[lang], f"{lang}: reason_{key}")
            for name in terms:
                self.assertIn("term_" + name, texts[lang], f"{lang}: term_{name}")

    def test_both_languages_have_the_same_keys(self):
        texts = dictionaries()
        self.assertEqual(sorted(texts["en"]), sorted(texts["de"]))


class CandidateTest(unittest.TestCase):
    def test_candidate_strategies_give_keys(self):
        gray = cv2.imread(TEST_JPG, cv2.IMREAD_GRAYSCALE)
        r = kader.find_best_crop(gray)
        self.assertTrue(r["reasons"])
        check(self, r["reasons"])


class EdgesTest(_Rolls):
    batch = BatchTest.batch

    def test_frame_edges_give_keys(self):
        by, _ = self.batch([scan(x, y, i) for i, (x, y) in enumerate(OFFSETS)])
        for r in by.values():
            self.assertTrue(r["reasons"])
            check(self, r["reasons"])

    def test_text_for_the_terminal(self):
        by, _ = self.batch([scan(x, y, i) for i, (x, y) in enumerate(OFFSETS)])
        for r in next(iter(by.values()))["reasons"]:
            self.assertTrue(kader.reason_text(r).startswith(r["key"]))


if __name__ == "__main__":
    unittest.main()

"""Unit tests for the plagiarism detector (run: python -m unittest -v)."""

import os
import unittest

from plagiarism_detector import (
    containment, direct_kgram_hashes, fingerprint, jaccard, kgram_hashes,
    normalise, tokenize, winnow,
)

HERE = os.path.dirname(os.path.abspath(__file__))


def read(name):
    with open(os.path.join(HERE, "samples", name), encoding="utf-8") as f:
        return f.read()


def score(a, b, k=5, w=4):
    fa = set(fingerprint(read(a), k, w)[1].values())
    fb = set(fingerprint(read(b), k, w)[1].values())
    return jaccard(fa, fb)


class TestPipeline(unittest.TestCase):
    def test_lexer_drops_comments_and_spaces(self):
        toks = tokenize("int x; /* c */ // d\n")
        self.assertEqual([t.kind for t in toks],
                         ["KW", "ID", "PUNCT"])

    def test_maximal_munch(self):
        lexemes = [t.lexeme for t in tokenize("i<=n++")]
        self.assertEqual(lexemes, ["i", "<=", "n", "++"])

    def test_string_with_comment_marks_is_one_token(self):
        toks = tokenize('printf("a // b /* c */");')
        self.assertEqual(sum(t.kind == "STR" for t in toks), 1)

    def test_normalisation(self):
        syms = [s for s, _ in normalise(tokenize("x = y + 10;"))]
        self.assertEqual(syms, ["ID", "=", "ID", "+", "NUM", ";"])

    def test_preprocessor_lines_dropped(self):
        syms = [s for s, _ in normalise(tokenize("#include <stdio.h>\nint x;"))]
        self.assertEqual(syms, ["int", "ID", ";"])

    def test_unknown_character_gives_err_token(self):
        self.assertIn("ERR", [t.kind for t in tokenize("int x @ ;")])

    def test_rolling_hash_matches_direct_hash(self):
        syms = [s for s, _ in normalise(tokenize(read("s1_original.c")))]
        for k in (3, 5, 7):
            self.assertEqual(kgram_hashes(syms, k),
                             direct_kgram_hashes(syms, k))

    def test_winnowing_guarantee(self):
        # a shared run of >= w+k-1 tokens must share at least one fingerprint
        k, w = 3, 3
        run = list("for(i=0;i<n;i++)")
        a = ["x"] * 7 + run + ["y"] * 5
        b = ["q"] * 2 + run + ["z"] * 9
        fa = set(winnow(kgram_hashes(a, k), w).values())
        fb = set(winnow(kgram_hashes(b, k), w).values())
        self.assertTrue(fa & fb)

    def test_too_short_file_has_no_fingerprints(self):
        self.assertEqual(fingerprint("int x;", 5, 4)[1], {})

    def test_containment_exposes_padding(self):
        small, big = {1, 2, 3}, {1, 2, 3, 4, 5, 6, 7, 8}
        self.assertEqual(containment(small, big), 1.0)
        self.assertLess(jaccard(small, big), 0.5)

    def test_layout_copy_detected(self):
        self.assertEqual(score("s1_original.c", "s2_layout_copy.c"), 1.0)

    def test_renamed_copy_detected(self):
        self.assertEqual(score("s1_original.c", "s3_renamed_copy.c"), 1.0)

    def test_modified_copy_flagged(self):
        s = score("s1_original.c", "s4_modified_copy.c")
        self.assertGreaterEqual(s, 0.40)
        self.assertLess(s, 1.0)

    def test_unrelated_programs_not_flagged(self):
        for other in ("s5_primes.c", "s6_matrix.c"):
            self.assertLess(score("s1_original.c", other), 0.40)
        self.assertLess(score("s5_primes.c", "s6_matrix.c"), 0.40)


if __name__ == "__main__":
    unittest.main()

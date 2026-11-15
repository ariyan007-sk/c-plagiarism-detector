#!/usr/bin/env python3
"""
Reproduce the experiments of the report:
  * Section 8.5 - raw text diff vs. tokens without normalisation vs. the
                  proposed normalised token stream
  * Section 8.6 - effect of the k-gram length k

Run:  python experiments.py
"""

import difflib
import os

from plagiarism_detector import (
    KEYWORDS, jaccard, kgram_hashes, normalise, tokenize, winnow,
)

HERE = os.path.dirname(os.path.abspath(__file__))
FILES = ["s1_original.c", "s2_layout_copy.c", "s3_renamed_copy.c",
         "s4_modified_copy.c", "s5_primes.c", "s6_matrix.c"]
SRC = {}
for name in FILES:
    with open(os.path.join(HERE, "samples", name), encoding="utf-8") as f:
        SRC[name] = f.read()


def fp_normalised(src, k, w):
    syms = [s for s, _ in normalise(tokenize(src))]
    return set(winnow(kgram_hashes(syms, k), w).values())


def fp_raw_tokens(src, k, w):
    """Same pipeline, but real identifier/literal text is kept."""
    syms = [t.lexeme for t in tokenize(src) if t.kind != "PP"]
    # hash by lexeme text instead of by class code
    h = [hash_text(syms[i:i + k]) for i in range(len(syms) - k + 1)]
    return set(winnow(h, w).values())


def hash_text(window, base=31, mod=1_000_003):
    h = 0
    for lexeme in window:
        for ch in lexeme + "\x00":
            h = (h * base + ord(ch)) % mod
    return h


def raw_diff(a, b):
    return difflib.SequenceMatcher(None, SRC[a], SRC[b]).ratio()


def main():
    base = FILES[0]
    print("Section 8.5 - comparison with other methods (k=5, w=4)")
    print(f"{'Pair':<30}{'Raw diff':>10}{'No norm.':>10}{'Normalised':>12}")
    for other in FILES[1:]:
        r = raw_diff(base, other)
        t = jaccard(fp_raw_tokens(SRC[base], 5, 4), fp_raw_tokens(SRC[other], 5, 4))
        n = jaccard(fp_normalised(SRC[base], 5, 4), fp_normalised(SRC[other], 5, 4))
        print(f"{'s1 vs ' + other:<30}{r:>10.2f}{t:>10.2f}{n:>12.2f}")

    print("\nSection 8.6 - choice of k (Jaccard, w=4)")
    ks = (3, 4, 5, 7, 9)
    print(f"{'Pair':<34}" + "".join(f"k={k:<5}" for k in ks))
    pairs = [("s1_original.c", "s3_renamed_copy.c", "s1 vs s3 (renamed copy)"),
             ("s1_original.c", "s4_modified_copy.c", "s1 vs s4 (Type 3 copy)"),
             ("s1_original.c", "s6_matrix.c", "s1 vs s6 (unrelated)"),
             ("s5_primes.c", "s6_matrix.c", "s5 vs s6 (unrelated)")]
    for a, b, label in pairs:
        row = "".join(
            f"{jaccard(fp_normalised(SRC[a], k, 4), fp_normalised(SRC[b], k, 4)):<7.2f}"
            for k in ks)
        print(f"{label:<34}{row}")


if __name__ == "__main__":
    main()

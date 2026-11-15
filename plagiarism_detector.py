#!/usr/bin/env python3
"""
Source Code Plagiarism Detection using Token Streams
Compiler Design (BTS50114) - Project Based Learning, Brainware University

Pipeline (same order as a compiler front end):
    1. Lexer       - regex-driven lexical analysis of C source
    2. Normaliser  - ID / NUM / STR / CHR replaced by class names
    3. k-grams     - Rabin-Karp rolling hash over the token stream
    4. Winnowing   - select fingerprints (Schleimer, Wilkerson, Aiken 2003)
    5. Similarity  - Jaccard + containment, verdict, matching lines

Only the Python 3 standard library is used.

Usage:
    python plagiarism_detector.py file1.c file2.c [file3.c ...] [-k 5] [-w 4]
"""

import argparse
import itertools
import os
import re
import sys
from collections import namedtuple

# --------------------------------------------------------------------------
# 1. LEXER
# --------------------------------------------------------------------------
KEYWORDS = {"int", "float", "double", "char", "void", "long", "short",
            "unsigned", "const", "struct", "if", "else", "for", "while",
            "do", "switch", "case", "default", "break", "continue",
            "return", "sizeof"}

# Ordered (name, regular expression) pairs - the lexical specification.
# The first pattern that matches at a position wins, so comments come before
# operators and long operators come before short ones (maximal munch).
TOKEN_SPEC = [
    ("COMMENT", r"//[^\n]*|/\*.*?\*/"),
    ("PP",      r"\#[^\n]*"),
    ("STR",     r'"(?:\\.|[^"\\])*"'),
    ("CHR",     r"'(?:\\.|[^'\\])'"),
    ("NUM",     r"\d+\.\d+|\d+"),
    ("ID",      r"[A-Za-z_]\w*"),
    ("OP",      r"\+\+|--|<=|>=|==|!=|&&|\|\||\+=|-=|\*=|/=|->|<<|>>"
                r"|[+\-*/%=<>!&|^~?:]"),
    ("PUNCT",   r"[(){}\[\];,.]"),
    ("WS",      r"\s+"),
    ("ERR",     r"."),
]
MASTER = re.compile("|".join(f"(?P<{n}>{p})" for n, p in TOKEN_SPEC), re.S)
Token = namedtuple("Token", "kind lexeme line")


def tokenize(source):
    """Return the list of Tokens (comments and white space are dropped)."""
    tokens, line = [], 1
    for m in MASTER.finditer(source):
        kind, text = m.lastgroup, m.group()
        if kind == "ID" and text in KEYWORDS:
            kind = "KW"
        if kind not in ("COMMENT", "WS"):
            tokens.append(Token(kind, text, line))
        line += text.count("\n")
    return tokens


# --------------------------------------------------------------------------
# 2. NORMALISER
# --------------------------------------------------------------------------
def normalise(tokens):
    """Abstract away names/values; drop preprocessor lines (boilerplate)."""
    out = []
    for t in tokens:
        if t.kind == "PP":
            continue
        sym = t.kind if t.kind in ("ID", "NUM", "STR", "CHR") else t.lexeme
        out.append((sym, t.line))
    return out


_VOCAB = (sorted(KEYWORDS) + ["ID", "NUM", "STR", "CHR"] +
          ["++", "--", "<=", ">=", "==", "!=", "&&", "||", "+=", "-=", "*=",
           "/=", "->", "<<", ">>"] + list("+-*/%=<>!&|^~?:(){}[];,."))
CODE = {s: i + 1 for i, s in enumerate(_VOCAB)}  # symbol -> integer code


# --------------------------------------------------------------------------
# 3. k-GRAMS AND ROLLING HASH (Rabin-Karp)
# --------------------------------------------------------------------------
BASE, MOD = 31, 1_000_003


def kgram_hashes(symbols, k):
    """Rabin-Karp rolling hash of every k consecutive tokens."""
    codes = [CODE.get(s, 0) for s in symbols]
    if len(codes) < k:
        return []
    high = pow(BASE, k - 1, MOD)
    h = 0
    for c in codes[:k]:
        h = (h * BASE + c) % MOD
    hashes = [h]
    for i in range(k, len(codes)):
        h = ((h - codes[i - k] * high) * BASE + codes[i]) % MOD
        hashes.append(h)
    return hashes


def direct_kgram_hashes(symbols, k):
    """Slow reference version (used only by the unit tests)."""
    codes = [CODE.get(s, 0) for s in symbols]
    result = []
    for i in range(len(codes) - k + 1):
        h = 0
        for c in codes[i:i + k]:
            h = (h * BASE + c) % MOD
        result.append(h)
    return result


# --------------------------------------------------------------------------
# 4. WINNOWING
# --------------------------------------------------------------------------
def winnow(hashes, w):
    """Select the minimum hash (rightmost on ties) of every window of w."""
    chosen, last = {}, -1
    for s in range(max(1, len(hashes) - w + 1)):
        window = hashes[s:s + w]
        if not window:
            break
        m = min(window)
        pos = s + (len(window) - 1 - window[::-1].index(m))
        if pos != last:
            chosen[pos] = m
            last = pos
    return chosen  # {position: hash}


def fingerprint(source, k=5, w=4):
    syms = normalise(tokenize(source))
    fp = winnow(kgram_hashes([s for s, _ in syms], k), w)
    return syms, fp


# --------------------------------------------------------------------------
# 5. SIMILARITY, VERDICT, MATCHING LINES
# --------------------------------------------------------------------------
def jaccard(a, b):
    return len(a & b) / len(a | b) if a | b else 0.0


def containment(a, b):  # share of the smaller set found in the other
    small, big = (a, b) if len(a) <= len(b) else (b, a)
    return len(small & big) / len(small) if small else 0.0


def verdict(score):
    if score >= 0.70:
        return "PLAGIARISM LIKELY"
    return "SUSPICIOUS" if score >= 0.40 else "ORIGINAL"


def matched_lines(syms, fp, other_hashes, k):
    """Source lines covered by k-grams whose fingerprint appears in the other."""
    lines = set()
    for pos, h in fp.items():
        if h in other_hashes:
            lines.update(l for _, l in syms[pos:pos + k])
    return sorted(lines)


def format_ranges(lines):
    """[3,4,5,8,9] -> '3-5, 8-9'"""
    if not lines:
        return "-"
    out, start, prev = [], lines[0], lines[0]
    for n in lines[1:]:
        if n == prev + 1:
            prev = n
            continue
        out.append(f"{start}-{prev}" if start != prev else f"{start}")
        start = prev = n
    out.append(f"{start}-{prev}" if start != prev else f"{start}")
    return ", ".join(out)


# --------------------------------------------------------------------------
# COMMAND-LINE DRIVER
# --------------------------------------------------------------------------
def main(argv=None):
    ap = argparse.ArgumentParser(
        description="Detect source-code plagiarism in C programs "
                    "using normalised token streams.")
    ap.add_argument("files", nargs="+", help="two or more C source files")
    ap.add_argument("-k", type=int, default=5, help="k-gram length (default 5)")
    ap.add_argument("-w", type=int, default=4, help="winnowing window (default 4)")
    args = ap.parse_args(argv)

    if len(args.files) < 2:
        ap.error("give at least two files to compare")

    data = {}
    for path in args.files:
        try:
            with open(path, encoding="utf-8", errors="replace") as f:
                src = f.read()
        except OSError as e:
            print(f"error: cannot read {path}: {e}", file=sys.stderr)
            return 1
        syms, fp = fingerprint(src, args.k, args.w)
        name = os.path.basename(path)
        data[name] = (syms, fp)
        n_k = max(0, len(syms) - args.k + 1)
        print(f"{name:<22} tokens={len(syms):>4} k-grams={n_k:>4} "
              f"fingerprints={len(fp):>3}")

    print()
    print(f"{'Pair':<44}{'Jaccard':>8}{'Contain.':>10}  Verdict")
    for (na, (sa, fa)), (nb, (sb, fb)) in itertools.combinations(data.items(), 2):
        ha, hb = set(fa.values()), set(fb.values())
        if not ha or not hb:
            print(f"{na + ' vs ' + nb:<44}{'-':>8}{'-':>10}  too short to compare")
            continue
        j, c = jaccard(ha, hb), containment(ha, hb)
        print(f"{na + ' vs ' + nb:<44}{j:>8.2f}{c:>10.2f}  {verdict(j)}")
        if j >= 0.40:
            la = format_ranges(matched_lines(sa, fa, hb, args.k))
            lb = format_ranges(matched_lines(sb, fb, ha, args.k))
            print(f"    matching lines: {na} [{la}]  {nb} [{lb}]")
    return 0


if __name__ == "__main__":
    sys.exit(main())

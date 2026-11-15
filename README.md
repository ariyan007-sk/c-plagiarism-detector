# Source Code Plagiarism Detection using Token Streams

**Compiler Design (BTS50114) - Project Based Learning**
B.Tech Computer Science & Engineering, Brainware University

Team: Ashutosh Pandey (404), Vivek Kumar (405), Ariyan Sk (406), Shruti Kumari (408)

A detector for **C programs** that borrows the first phase of a compiler, *lexical analysis*.
Each program is converted into a token stream, so comments and layout disappear. Identifiers,
numbers and strings are replaced by class symbols, so renaming has no effect. The stream is cut
into k-grams, hashed with a **Rabin-Karp rolling hash**, reduced to fingerprints by **winnowing**
(the idea behind MOSS), and two programs are compared with **Jaccard similarity**. The lines that
caused a match are reported so a teacher can verify the result.

Pure Python 3 standard library. No packages to install.

## Pipeline

```
 C file -> 1 Lexer -> 2 Normaliser -> 3 k-gram rolling hash -> 4 Winnowing -> 5 Jaccard + matching lines -> 6 Verdict
          (regex/DFA)  (ID,NUM,STR)     (Rabin-Karp)            (fingerprints)
```

| Stage | What it does | Function |
|-------|--------------|----------|
| Lexer | Regex-driven scanner, maximal munch, drops comments/whitespace, records line numbers | `tokenize` |
| Normaliser | Drops `#` lines; ID / NUM / STR / CHR become class names | `normalise` |
| k-gram hash | Rolling hash of every k consecutive tokens, O(1) per window | `kgram_hashes` |
| Winnowing | Keeps the minimum hash of every window of w hashes | `winnow` |
| Similarity | Jaccard, containment, verdict, matching line ranges | `jaccard`, `containment`, `verdict`, `matched_lines` |

Defaults: **k = 5, w = 4**, hash base 31, modulus 1,000,003.
Thresholds: J >= 0.70 *plagiarism likely*, 0.40 to 0.70 *suspicious*, below 0.40 *original*.

## Usage

```bash
python plagiarism_detector.py samples/s1_original.c samples/s3_renamed_copy.c samples/s5_primes.c
python plagiarism_detector.py samples/*.c -k 5 -w 4      # all pairs
python -m unittest -v                                    # 14 unit tests
python experiments.py                                    # reproduces report tables 8.5 and 8.6
```

Example output (`python plagiarism_detector.py samples/s1_original.c samples/s3_renamed_copy.c samples/s6_matrix.c`):

```
Pair                                         Jaccard  Contain.  Verdict
s1_original.c vs s3_renamed_copy.c              1.00      1.00  PLAGIARISM LIKELY
    matching lines: s1_original.c [4-8, 10-15, 17-25, 27-31]  s3_renamed_copy.c [4-8, 10-15, 17-25, 27-31]
s1_original.c vs s6_matrix.c                    0.32      0.61  ORIGINAL
s3_renamed_copy.c vs s6_matrix.c                0.32      0.61  ORIGINAL
```

## Test programs (`samples/`)

| File | Role | Disguise |
|------|------|----------|
| `s1_original.c` | Original | Reads 5 marks, bubble-sorts, prints average |
| `s2_layout_copy.c` | Type 1 copy | New comments, Allman braces, blank lines |
| `s3_renamed_copy.c` | Type 2 copy | All variables renamed, messages changed |
| `s4_modified_copy.c` | Type 3 copy | `for` to `while`, `sum +=`, swapped comparison, moved statements, extra loop |
| `s5_primes.c` | Unrelated | Prime numbers with a helper function |
| `s6_matrix.c` | Unrelated | 3x3 matrix multiplication |

All six compile with `gcc -fsyntax-only`.

## Results (k = 5, w = 4)

| Pair | Jaccard | Verdict |
|------|---------|---------|
| s1 vs s2 (layout copy) | 1.00 | Plagiarism likely |
| s1 vs s3 (renamed copy) | 1.00 | Plagiarism likely |
| s1 vs s4 (structural edits) | 0.45 | Suspicious, manual review |
| s1 vs s5 (unrelated) | 0.12 | Original |
| s1 vs s6 (unrelated) | 0.32 | Original |
| s5 vs s6 (unrelated) | 0.05 | Original |

Comparison with a plain character diff (`difflib.SequenceMatcher`): the raw diff scores the renamed
copy *lower* (0.15) than an unrelated program (0.22), so no threshold can separate them. Normalised
tokens score 1.00 versus at most 0.32. Run `python experiments.py` for the full tables, including
the effect of k (small k is noisy, large k misses Type 3 copies).

## What it detects

| Type | Copier changes | Detected |
|------|----------------|----------|
| 1 | Comments, whitespace, layout | Yes (1.00) |
| 2 | Identifier names, literals, strings | Yes (1.00) |
| 3 | Statements added, removed, re-ordered | Partly, score drops and is flagged |
| 4 | Different algorithm, same behaviour | No (needs semantic analysis) |

## Limitations and future scope

- Type 4 clones are not detected; heavy statement re-ordering lowers the score.
- Thresholds were tuned on six programs only and should be re-tuned on a larger set.
- The small hash modulus allows rare collisions; use a 64-bit hash for big collections.
- Shared instructor template code can raise honest scores; exclude it.
- Future: AST/CFG comparison, inverted index for large classes, Java/Python lexers, HTML report.

## Project layout

```
plagiarism_detector.py   lexer, normaliser, rolling hash, winnowing, similarity, CLI
test_detector.py         unit tests
experiments.py           regenerates the comparison and choice-of-k tables
samples/                 six C test programs
```

## References

1. Aho, Lam, Sethi, Ullman - *Compilers: Principles, Techniques, and Tools*, 2nd ed.
2. Schleimer, Wilkerson, Aiken - "Winnowing: Local Algorithms for Document Fingerprinting", SIGMOD 2003.
3. Prechelt, Malpohl, Philippsen - "Finding Plagiarisms among a Set of Programs with JPlag", JUCS 2002.
4. Karp, Rabin - "Efficient randomized pattern-matching algorithms", IBM J. Res. Dev., 1987.

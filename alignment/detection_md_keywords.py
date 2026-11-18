#!/usr/bin/env python3
"""Compare the keywords used in RSQKit pages with the training keywords CSV.

This script only reports differences: it does not modify any file.

Usage (run it from any folder; the script lives in alignment/):
    python alignment/detection_md_keywords.py --rsqkit /path/to/RSQKit \
        [--csv csv/keywords.csv] [--threshold 0.7] [--out keywords_report.csv]

By default the CSV is read from ../csv/keywords.csv (relative to this
script) and the report is written in the same folder as this script.

--rsqkit is the RSQKit repository folder: the one that contains pages/, whose
.md files hold the keywords in their front matter.

Report: one row per distinct keyword that is NOT in the CSV, for the pages
where it is not already accompanied by a close canonical keyword (one that is
also in the CSV). num_pages and pages therefore list only the pages still
needing review.
Columns: keyword in md not in csv, suggestion from csv keywords, similarity,
related_by_words, num_pages, pages

Two kinds of hints are given for each missing keyword:
  - suggestion / similarity: the closest CSV keyword by spelling (difflib),
    only if similarity >= threshold and it passes a morphology check (word
    containment, or a prefix between the words the two keywords do not share).
    This drops false friends such as "software citation" -> "software testing".
  - related_by_words: CSV keywords whose words are all contained in the
    keyword, or the other way round (e.g. "citation.cff" contains "cff";
    "citation" is contained in "code citation").

Rows are sorted: spelling suggestions first (most similar first), then rows
with a word relation, then the rest (most used first within each group).
"""
import argparse
import csv
import difflib
import re
import sys
from collections import defaultdict
from pathlib import Path

import yaml

# Matches the YAML front matter at the top of a Markdown file
FM = re.compile(r"\A---\s*\n(.*?)\n---\s*\n", re.S)
DEFAULT_THRESHOLD = 0.7
# Paths relative to this script (it lives in alignment/, next to csv/)
SCRIPT_DIR = Path(__file__).resolve().parent
DEFAULT_CSV = SCRIPT_DIR.parent / "csv" / "keywords.csv"
DEFAULT_OUT = SCRIPT_DIR / "keywords_report.csv"
# Comment written as the first row of the report
# REPORT_NOTE = (
#     "# NOTE: 'suggestion' (similar spelling) and 'related_by_words' are hints, "
#     "not verdicts. Each missing keyword needs a manual decision."
# )


def load_training_keywords(path):
    """Return the set of keywords (lowercase) from the training CSV."""
    with open(path, newline="", encoding="utf-8-sig") as f:
        rows = list(csv.reader(f))
    # Skip the header row and empty lines
    return {r[0].strip().lower() for r in rows[1:] if r and r[0].strip()}


def load_page_keywords(root):
    """Return {page_path: [keywords]} for pages with keywords in the front matter."""
    pages_dir = Path(root, "pages")
    if not pages_dir.is_dir():
        sys.exit(f"[ERROR] No 'pages' folder found in {root}. --rsqkit must point to the RSQKit repository.")
    pages = {}
    for md in sorted(pages_dir.rglob("*.md")):
        m = FM.match(md.read_text(encoding="utf-8", errors="ignore"))
        if not m:
            continue
        try:
            fm = yaml.safe_load(m.group(1)) or {}
        except yaml.YAMLError:
            print(f"[WARN] Invalid front matter: {md}", file=sys.stderr)
            continue
        kws = fm.get("keywords")
        if kws:
            if isinstance(kws, str):
                kws = [k.strip() for k in kws.split(",")]
            pages[md.relative_to(root).as_posix()] = [str(k).strip() for k in kws]
    return pages


def words(keyword):
    """Split a keyword into a set of words (separators: spaces, dots, dashes, slashes...).

    '+' and '#' are kept so that 'c++' and 'c#' stay whole.
    """
    return {w for w in re.split(r"[^a-z0-9+#]+", keyword.lower()) if w}


def related_by_words(kw, training_words):
    """Return the CSV keywords whose word set is contained in kw's, or vice versa."""
    kw_words = words(kw)
    related = []
    for t, t_words in training_words.items():
        if t_words and (t_words <= kw_words or kw_words <= t_words):
            related.append(t)
    return sorted(related)


def threshold_type(value):
    """argparse type: a float between 0 and 1."""
    x = float(value)
    if not 0 <= x <= 1:
        raise argparse.ArgumentTypeError("threshold must be between 0 and 1")
    return x


def morphologically_related(kw, candidate):
    """Cheap sanity check to discard false friends such as
    'software citation' -> 'software testing'.

    True when one word set contains the other, or when, after dropping the
    words both keywords already share, some remaining word is a prefix of
    another ('test' / 'testing', 'version' / 'versioning').
    """
    a, b = words(kw), words(candidate)
    if a and (a <= b or b <= a):
        return True
    shared = a & b
    rest_a, rest_b = a - shared, b - shared
    return any(x.startswith(y) or y.startswith(x) for x in rest_a for y in rest_b)


def best_suggestion(kw, pool, threshold):
    """Best spelling suggestion from pool, after the morphology check."""
    candidates = [t for t in pool if morphologically_related(kw, t)]
    close = difflib.get_close_matches(kw, candidates, n=1, cutoff=threshold)
    if not close:
        return "", 0.0
    return close[0], difflib.SequenceMatcher(None, close[0], kw).ratio()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--rsqkit", required=True, help="Path to the RSQKit repository (the folder that contains pages/ with the .md files)")
    ap.add_argument("--csv", default=DEFAULT_CSV, help="Path to the training keywords.csv (default: ../csv/keywords.csv)")
    ap.add_argument("--out", default=DEFAULT_OUT, help="Output report path (default: same folder as this script)")
    ap.add_argument(
        "--threshold",
        type=threshold_type,
        default=DEFAULT_THRESHOLD,
        help=f"Minimum similarity (0-1) to suggest a CSV keyword (default: {DEFAULT_THRESHOLD})",
    )
    a = ap.parse_args()

    training = load_training_keywords(a.csv)
    training_words = {t: words(t) for t in training}
    pages = load_page_keywords(a.rsqkit)

    # Group pages by keyword (lowercase)
    by_kw = defaultdict(set)
    for page, kws in pages.items():
        for kw in kws:
            by_kw[kw.lower()].add(page)

    page_kws = {p: {k.lower() for k in kws} for p, kws in pages.items()}
    covered = set(by_kw) & training   # keywords already in csv

    rows = []
    skipped_pages = 0
    for kw, ps in by_kw.items():
        if kw in training:
            continue  # already in the CSV: not reported

        covered_like = set(difflib.get_close_matches(kw, covered, n=len(covered),
                                                 cutoff=a.threshold))
        before = len(ps)
        ps = {p for p in ps if not (page_kws[p] & covered_like)}
        skipped_pages += before - len(ps)
        if not ps:
            continue

        sugg, sim = best_suggestion(kw, covered_like, a.threshold)
        if not sugg:
            sugg, sim = best_suggestion(kw, training, a.threshold)

        rel = related_by_words(kw, training_words)
        rows.append([kw, len(ps), ";".join(sorted(ps)), sugg, sim, rel])

    # Spelling suggestions first (most similar first), then word relations, then the rest
    # Group 0: spelling suggestion; group 1: only word relation; group 2: the rest
    def sort_key(r):
        group = 0 if r[3] else (1 if r[5] else 2)
        return (group, -r[4], -r[1], r[0])

    rows.sort(key=sort_key)

    with open(a.out, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        # First row is a comment (starts with '#'), before the header
        # w.writerow([REPORT_NOTE])
        w.writerow(["keyword in Rsqkit pages md but not in Everse_training csv", "suggestion from Everse Training csv keywords", "similarity", "related_by_words", "num_pages", "pages"])
        for kw, n, ps, sugg, sim, rel in rows:
            w.writerow([kw, sugg, f"{sim:.2f}" if sugg else "", ";".join(rel), n, ps])

    n_sugg = sum(1 for r in rows if r[3])
    n_rel = sum(1 for r in rows if r[5])
    n_missing = sum(1 for kw in by_kw if kw not in training)
    print(f"Distinct keywords in RSQKit: {len(by_kw)} -> in CSV: {len(by_kw) - n_missing}, missing: {n_missing}")
    print(f"Reported rows: {len(rows)} (after page screening)")
    print(f"Pages with keywords: {len(pages)}")
    print(f"Threshold: {a.threshold} -> missing keywords with a similar spelling in the CSV: {n_sugg}")
    print(f"Missing keywords related by words to a CSV keyword: {n_rel}")
    print(f"Pages skipped (canonical form already in the md): {skipped_pages}")
    print(f"Report written to: {a.out}")


if __name__ == "__main__":
    main()
#!/usr/bin/env python3
"""Report the training CSV keywords that are NOT used in any RSQKit page.

This is the reverse of detection_keywords_v3.py. It only reports
differences: it does not modify any file.

Usage (run it from any folder; the script lives in alignment/):
    python alignment/detection_unused_keywords.py --rsqkit /path/to/RSQKit \
        [--csv csv/keywords.csv] [--threshold 0.7] [--out unused_keywords_report.csv]

By default the CSV is read from ../csv/keywords.csv (relative to this
script) and the report is written in the same folder as this script.

Report: one row per CSV keyword that no page uses (case-insensitive
comparison).
Columns: keyword, suggestion, similarity, related_by_words

The hints point to RSQKit keywords that are NOT in the CSV (the ones that
do not match anything), because those are the possible variants:
  - suggestion / similarity: the closest of them by spelling (difflib),
    only if similarity >= threshold (e.g. "container" vs "containers").
  - related_by_words: those whose words are all contained in the CSV
    keyword, or the other way round (e.g. "cff" vs "citation.cff").

Rows are sorted: spelling suggestions first (most similar first), then rows
with a word relation, then the rest in alphabetical order.
"""
import argparse
import csv
import difflib
import re
import sys
from pathlib import Path

import yaml

# Matches the YAML front matter at the top of a Markdown file
FM = re.compile(r"\A---\s*\n(.*?)\n---\s*\n", re.S)
DEFAULT_THRESHOLD = 0.7
# Paths relative to this script (it lives in alignment/, next to csv/)
SCRIPT_DIR = Path(__file__).resolve().parent
DEFAULT_CSV = SCRIPT_DIR.parent / "csv" / "keywords.csv"
DEFAULT_OUT = SCRIPT_DIR / "unused_keywords_report.csv"
# Comment written as the first row of the report
REPORT_NOTE = (
    "# NOTE: 'suggestion' (similar spelling) and 'related_by_words' are hints, "
    "not verdicts. Each unused keyword needs a manual decision."
)


def load_training_keywords(path):
    """Return the set of keywords (lowercase) from the training CSV."""
    with open(path, newline="", encoding="utf-8-sig") as f:
        rows = list(csv.reader(f))
    # Skip the header row and empty lines
    return {r[0].strip().lower() for r in rows[1:] if r and r[0].strip()}


def load_page_keywords(root):
    """Return {page_path: [keywords]} for pages with keywords in the front matter."""
    pages = {}
    for md in sorted(Path(root, "pages").rglob("*.md")):
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


def related_by_words(kw, candidate_words):
    """Return the candidates whose word set is contained in kw's, or vice versa."""
    kw_words = words(kw)
    related = []
    for c, c_words in candidate_words.items():
        if c_words and (c_words <= kw_words or kw_words <= c_words):
            related.append(c)
    return sorted(related)


def threshold_type(value):
    """argparse type: a float between 0 and 1."""
    x = float(value)
    if not 0 <= x <= 1:
        raise argparse.ArgumentTypeError("threshold must be between 0 and 1")
    return x


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--rsqkit", required=True, help="Path to the RSQKit repository")
    ap.add_argument("--csv", default=DEFAULT_CSV, help="Path to the training keywords.csv (default: ../csv/keywords.csv)")
    ap.add_argument("--out", default=DEFAULT_OUT, help="Output report path (default: same folder as this script)")
    ap.add_argument(
        "--threshold",
        type=threshold_type,
        default=DEFAULT_THRESHOLD,
        help=f"Minimum similarity (0-1) to suggest an RSQKit keyword (default: {DEFAULT_THRESHOLD})",
    )
    a = ap.parse_args()

    training = load_training_keywords(a.csv)
    pages = load_page_keywords(a.rsqkit)

    used = {kw.lower() for kws in pages.values() for kw in kws}
    unused = sorted(training - used)
    # Candidates for the hints: RSQKit keywords that do not match the CSV
    candidates = sorted(used - training)
    candidate_words = {c: words(c) for c in candidates}

    rows = []
    for kw in unused:
        sugg, sim = "", 0.0
        close = difflib.get_close_matches(kw, candidates, n=1, cutoff=a.threshold)
        if close:
            sugg = close[0]
            sim = difflib.SequenceMatcher(None, close[0], kw).ratio()
        rel = related_by_words(kw, candidate_words)
        rows.append([kw, sugg, sim, rel])

    # Group 0: spelling suggestion; group 1: only word relation; group 2: the rest
    def sort_key(r):
        group = 0 if r[1] else (1 if r[3] else 2)
        return (group, -r[2], r[0])

    rows.sort(key=sort_key)

    with open(a.out, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        # First row is a comment (starts with '#'), before the header
        w.writerow([REPORT_NOTE])
        w.writerow(["keyword in csv not in md", "suggestion", "similarity", "related_by_words"])
        for kw, sugg, sim, rel in rows:
            w.writerow([kw, sugg, f"{sim:.2f}" if sugg else "", ";".join(rel)])

    n_sugg = sum(1 for r in rows if r[1])
    n_rel = sum(1 for r in rows if r[3])
    print(f"Pages with keywords: {len(pages)}")
    print(f"Keywords in CSV: {len(training)} -> used in RSQKit: {len(training) - len(unused)}, unused: {len(unused)}")
    print(f"Threshold: {a.threshold} -> unused keywords with a similar spelling in RSQKit: {n_sugg}")
    print(f"Unused keywords related by words to an RSQKit keyword: {n_rel}")
    print(f"Report written to: {a.out}")


if __name__ == "__main__":
    main()
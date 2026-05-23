#!/usr/bin/env python3
"""
search_manual.py — Search the converted manual text for keywords.

Usage:
  python scripts/search_manual.py "velocidad máxima" [options]

Options:
  --txt PATH       Text file to search (default: manual_conductor.txt)
  --context N      Lines of context around each match (default: 5)
  --max-matches N  Stop after N matches (default: 20)
  --page           Show page number for each match
"""

import argparse
import io
import re
import sys
from pathlib import Path

# Force UTF-8 output on Windows consoles
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

ROOT = Path(__file__).parent.parent


def search(txt_path: Path, query: str, context: int, max_matches: int, show_page: bool) -> None:
    if not txt_path.exists():
        print(f"Error: text file not found: {txt_path}", file=sys.stderr)
        print("Run: python scripts/pdf_to_text.py", file=sys.stderr)
        sys.exit(1)

    lines = txt_path.read_text(encoding="utf-8").splitlines()
    pattern = re.compile(re.escape(query), re.IGNORECASE)

    # Build page index: line_number -> page_number
    page_at: dict[int, int] = {}
    cur_page = 0
    for i, line in enumerate(lines):
        m = re.match(r"^--- PAGE (\d+) ---$", line.strip())
        if m:
            cur_page = int(m.group(1))
        page_at[i] = cur_page

    found = 0
    for i, line in enumerate(lines):
        if pattern.search(line):
            found += 1
            if found > max_matches:
                print(f"\n... (stopped after {max_matches} matches)")
                break

            page_label = f"  [p.{page_at[i]}]" if show_page else ""
            print(f"\n{'='*60}")
            print(f"Match {found}{page_label}  (line {i+1})")
            print(f"{'='*60}")

            start = max(0, i - context)
            end = min(len(lines), i + context + 1)
            for j in range(start, end):
                marker = ">>>" if j == i else "   "
                print(f"{marker} {lines[j]}")

    if found == 0:
        print(f"No matches for: {query!r}")
    else:
        capped = min(found, max_matches)
        print(f"\n{capped} match(es) shown for: {query!r}")


def main():
    parser = argparse.ArgumentParser(description="Search manual text for keywords")
    parser.add_argument("query", help="Search term (case-insensitive)")
    parser.add_argument("--txt", default="manual_conductor.txt")
    parser.add_argument("--context", type=int, default=5, metavar="N")
    parser.add_argument("--max-matches", type=int, default=20, metavar="N")
    parser.add_argument("--page", action="store_true", default=True)
    args = parser.parse_args()

    txt_path = ROOT / args.txt
    search(txt_path, args.query, args.context, args.max_matches, args.page)


if __name__ == "__main__":
    main()

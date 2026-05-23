#!/usr/bin/env python3
"""
pdf_to_text.py — Convert a PDF to a plain-text file using PyMuPDF.

Usage:
  python scripts/pdf_to_text.py [--pdf PATH] [--out PATH]

Defaults:
  --pdf  manual_conductor.pdf   (relative to repo root)
  --out  manual_conductor.txt   (relative to repo root)
"""

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent


def convert(pdf_path: Path, out_path: Path) -> int:
    try:
        import fitz  # PyMuPDF
    except ImportError:
        print("Error: PyMuPDF not installed. Run: pip install pymupdf", file=sys.stderr)
        sys.exit(1)

    doc = fitz.open(str(pdf_path))
    total = doc.page_count
    print(f"PDF: {pdf_path.name}  |  {total} pages")

    with open(out_path, "w", encoding="utf-8") as f:
        for i, page in enumerate(doc, 1):
            text = page.get_text("text")
            if text.strip():
                f.write(f"\n\n--- PAGE {i} ---\n\n")
                f.write(text)
            if i % 20 == 0:
                print(f"  {i}/{total} pages...", flush=True)

    doc.close()
    size_kb = out_path.stat().st_size // 1024
    print(f"Done: {out_path}  ({size_kb} KB)")
    return total


def main():
    parser = argparse.ArgumentParser(description="Convert PDF to plain text via PyMuPDF")
    parser.add_argument("--pdf", default="manual_conductor.pdf")
    parser.add_argument("--out", default="manual_conductor.txt")
    args = parser.parse_args()

    pdf_path = ROOT / args.pdf
    out_path = ROOT / args.out

    if not pdf_path.exists():
        print(f"Error: PDF not found: {pdf_path}", file=sys.stderr)
        sys.exit(1)

    convert(pdf_path, out_path)


if __name__ == "__main__":
    main()

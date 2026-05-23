#!/usr/bin/env python3
"""
check_translations.py — audits every question.json for translation issues
using the `claude` CLI (Claude Code). No API key required.

Checks (Spanish is always the truth source):
  1. Language-field integrity   — es/en/ru fields contain the expected language
  2. Correct-answer validity    — the response marked correct=true is actually right
  3. Translation accuracy       — EN and RU faithfully convey the ES meaning

Usage:
  python scripts/check_translations.py [options]

Options:
  --start N        First question folder index (default: 0)
  --end N          Last question folder index (exclusive, default: all)
  --batch-size N   Questions per claude call (default: 10)
  --output FILE    JSON report path, relative to repo root (default: translation_report.json)
  --lang LANG      Target language(s): en | ru | both (default: both)

Requires:
  claude CLI installed and authenticated (comes with Claude Code)
"""

from __future__ import annotations

import json
import os
import re
import sys
import shutil
import argparse
import subprocess
from pathlib import Path
from typing import Optional

ROOT = Path(__file__).parent.parent
QUESTIONS_DIR = ROOT / "questions"

TRIVIAL_ES = re.compile(
    r"^(opci[oó]n\s+[abc]|verdadero|falso|s[ií]|no)\.?$",
    re.IGNORECASE,
)

PROMPT_PREFIX = """\
You are auditing driving-exam questions for translation errors.
Spanish (es) is ALWAYS the authoritative source.

For each question perform THREE checks:

CHECK 1 — Language-field integrity
  Confirm that each "es" field is actually Spanish, "en" is English, "ru" is Russian.
  Flag fields that contain text in the wrong language.

CHECK 2 — Correct-answer validity
  The response with [CORRECT] should be the right answer given the ES question + explanation.
  Flag if the correct marker appears to be on the wrong response.

CHECK 3 — Translation accuracy
  EN and RU translations must faithfully convey the ES meaning. Flag:
  - Wrong numbers, speeds, distances, ages, percentages
  - Incorrect traffic / road / legal terminology
  - Meaning-changing omissions or additions
  - Phrasing that changes which answer a test-taker would choose

Do NOT flag minor stylistic variation. Ignore trivial labels (Option A/B/C, True/False).

Output ONLY a valid JSON array, nothing else (no markdown fences, no prose).
Each element:
  {"folder":"NNNN","check":1|2|3,"field":"text|responses[N].text|explanation.text","lang":"en|ru|es|correct_marker","issue":"concise description","es":"ES snippet","translation":"problematic snippet"}

If no issues found: output exactly []

Questions to review:
"""


def load_questions() -> list[dict]:
    questions = []
    for folder in sorted(QUESTIONS_DIR.iterdir()):
        if not folder.name.isdigit():
            continue
        q_file = folder / "question.json"
        if q_file.exists():
            with open(q_file, encoding="utf-8") as f:
                data = json.load(f)
            data["_folder"] = folder.name
            questions.append(data)
    return questions


def format_question(q: dict, langs: list[str]) -> str:
    folder = q["_folder"]
    lines = [f"=== Q{folder} ==="]

    t = q["text"]
    lines.append(f"text.es: {t['es']}")
    for lang in langs:
        lines.append(f"text.{lang}: {t.get(lang, '[MISSING]')}")

    has_correct = False
    for i, resp in enumerate(q.get("responses", [])):
        rt = resp["text"]
        marker = " [CORRECT]" if resp.get("correct") else ""
        if resp.get("correct"):
            has_correct = True
        lines.append(f"responses[{i}].text.es:{marker} {rt['es']}")
        if not TRIVIAL_ES.match(rt["es"].strip()):
            for lang in langs:
                lines.append(f"responses[{i}].text.{lang}: {rt.get(lang, '[MISSING]')}")

    if not has_correct:
        lines.append("NOTE: no response is marked [CORRECT]")

    if "explanation" in q:
        et = q["explanation"]["text"]
        lines.append(f"explanation.text.es: {et['es']}")
        for lang in langs:
            lines.append(f"explanation.text.{lang}: {et.get(lang, '[MISSING]')}")

    return "\n".join(lines)


def build_prompt(batch: list[dict], langs: list[str]) -> str:
    blocks = [PROMPT_PREFIX]
    for q in batch:
        blocks.append(format_question(q, langs))
    return "\n\n".join(blocks)


def parse_json_response(raw: str) -> list[dict]:
    text = raw.strip()
    # Strip accidental markdown fences
    text = re.sub(r"^```(?:json)?\s*", "", text)
    text = re.sub(r"\s*```$", "", text).strip()
    try:
        result = json.loads(text)
        return result if isinstance(result, list) else []
    except json.JSONDecodeError:
        m = re.search(r"\[.*\]", text, re.DOTALL)
        if m:
            try:
                return json.loads(m.group())
            except json.JSONDecodeError:
                pass
    return []


def call_claude(prompt: str, model: Optional[str] = None) -> str:
    cmd = ["claude", "-p", prompt]
    if model:
        cmd += ["--model", model]
    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or f"claude exited {result.returncode}")
    return result.stdout


def check_batch(batch: list[dict], langs: list[str], model: Optional[str]) -> list[dict]:
    prompt = build_prompt(batch, langs)
    try:
        raw = call_claude(prompt, model)
        issues = parse_json_response(raw)
        if not isinstance(issues, list):
            return []
        return issues
    except RuntimeError as exc:
        folders = [q["_folder"] for q in batch]
        print(f"\n  Error on Q{folders[0]}–{folders[-1]}: {exc}", file=sys.stderr)
        return []


CHECK_LABELS = {1: "Language field", 2: "Correct answer", 3: "Translation"}


def print_report(all_issues: list[dict]) -> None:
    if not all_issues:
        print("\nAll checked questions look correct — no issues found.")
        return

    by_folder: dict[str, list] = {}
    for iss in all_issues:
        by_folder.setdefault(iss.get("folder", "?"), []).appчend(iss)

    by_check: dict[int, int] = {}
    for iss in all_issues:
        k = iss.get("check", 3)
        by_check[k] = by_check.get(k, 0) + 1

    print("\n" + "=" * 64)
    print(f"REPORT: {len(all_issues)} issue(s) in {len(by_folder)} question(s)")
    for check_id, count in sorted(by_check.items()):
        print(f"  Check {check_id} — {CHECK_LABELS.get(check_id, '?')}: {count}")
    print("=" * 64)

    for folder in sorted(by_folder.keys()):
        print(f"\nQ{folder}:")
        for iss in sorted(
            by_folder[folder],
            key=lambda x: (x.get("check", 3), x.get("field", "")),
        ):
            check_id = iss.get("check", 3)
            lang_tag = f"[{iss.get('lang', '?').upper()}]"
            field = iss.get("field", "?")
            desc = iss.get("issue", "")
            es_snip = iss.get("es", "")
            tr_snip = iss.get("translation", "")
            label = CHECK_LABELS.get(check_id, f"Check {check_id}")
            print(f"  [{label}] {lang_tag} {field}")
            print(f"    Issue: {desc}")
            if es_snip:
                print(f"    ES:    {es_snip}")
            if tr_snip:
                print(f"    Got:   {tr_snip}")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Audit ES→EN/RU translations using the `claude` CLI"
    )
    parser.add_argument("--start", type=int, default=0, metavar="N")
    parser.add_argument("--end", type=int, default=None, metavar="N")
    parser.add_argument("--batch-size", type=int, default=10, metavar="N")
    parser.add_argument("--output", default="translation_report.json", metavar="FILE")
    parser.add_argument("--model", default=None, metavar="MODEL",
                        help="Override claude model (e.g. claude-opus-4-7)")
    parser.add_argument("--lang", choices=["en", "ru", "both"], default="both")
    args = parser.parse_args()

    if not shutil.which("claude"):
        print("Error: `claude` CLI not found in PATH. Install Claude Code first.", file=sys.stderr)
        sys.exit(1)

    langs = ["en", "ru"] if args.lang == "both" else [args.lang]

    all_questions = load_questions()
    print(f"Loaded {len(all_questions)} questions")

    subset = all_questions[args.start : args.end]
    end_idx = (args.end or len(all_questions)) - 1
    print(
        f"Checking Q{args.start}–{end_idx}"
        f" | langs: {', '.join(langs)}"
        f" | batch: {args.batch_size}"
        + (f" | model: {args.model}" if args.model else "")
    )

    all_issues: list[dict] = []
    bs = args.batch_size
    total_batches = (len(subset) + bs - 1) // bs

    for i in range(0, len(subset), bs):
        batch = subset[i : i + bs]
        batch_num = i // bs + 1
        folders = [q["_folder"] for q in batch]
        print(
            f"  [{batch_num:3d}/{total_batches}] Q{folders[0]}–{folders[-1]} ...",
            end=" ",
            flush=True,
        )
        issues = check_batch(batch, langs, args.model)
        all_issues.extend(issues)
        print(f"{len(issues)} issue(s)")

    output_path = ROOT / args.output
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(all_issues, f, ensure_ascii=False, indent=2)

    print(f"\nTotal: {len(all_issues)} issue(s) | Report → {output_path}")
    print_report(all_issues)


if __name__ == "__main__":
    main()

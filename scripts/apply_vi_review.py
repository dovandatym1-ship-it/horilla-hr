#!/usr/bin/env python3
"""Promote only explicitly reviewed Vietnamese strings into production gettext.

Never accept a bulk MT draft on its own: each row must carry a reviewer and
APPROVE/REWRITE decision with a final checked Vietnamese translation.
"""
from __future__ import annotations

import argparse
import csv
import json
import re
from collections import Counter
from pathlib import Path

import polib

PLACEHOLDER = re.compile(
    r"%\([a-zA-Z_][a-zA-Z_0-9]*\)[#0 +.-]*[a-zA-Z]|"
    r"%(?:\d+\$)?[sdfr]|\{[a-zA-Z_][a-zA-Z_0-9]*\}"
)
VI_DIACRITIC = re.compile("[À-ỹĐđ]")
ENGLISH = re.compile("[A-Za-z]{3,}")
DECISIONS = {"APPROVE", "REWRITE"}


def validate(source, translation, reviewer):
    errors = []
    if not source or not translation.strip() or translation == source:
        errors.append("empty_or_unchanged")
    if not reviewer.strip() or len(reviewer.strip()) < 2:
        errors.append("reviewer_required")
    if sorted(PLACEHOLDER.findall(source)) != sorted(
        PLACEHOLDER.findall(translation)
    ):
        errors.append("placeholder_mismatch")
    if ENGLISH.search(source) and not VI_DIACRITIC.search(translation):
        errors.append("not_a_vietnamese_sentence")
    if re.search(r"\{%|\{\{", translation):
        if sorted(re.findall(r"\{%.*?%\}|\{\{.*?\}\}", source)) != sorted(
            re.findall(r"\{%.*?%\}|\{\{.*?\}\}", translation)
        ):
            errors.append("template_tag_mismatch")
    return errors


def apply(queue, catalogue, *, approve, report_path):
    original = polib.pofile(str(catalogue))
    existing = set(entry.msgid for entry in original if entry.msgid)
    accepted, errors = {}, {}
    with queue.open(encoding="utf-8-sig", newline="") as file:
        for i, row in enumerate(csv.DictReader(file), start=2):
            decision = (row.get("decision") or "").strip().upper()
            if decision not in DECISIONS:
                continue
            source = row["source"]
            result = (
                (row.get("approved_vietnamese") or "").strip()
                if decision == "REWRITE" else
                (row.get("approved_vietnamese") or row.get("suggestion") or "").strip()
            )
            problems = validate(source, result, row.get("reviewer") or "")
            if source in existing:
                problems.append("already_in_catalogue")
            if source in accepted:
                problems.append("duplicate_reviewed_key")
            if problems:
                errors[i] = problems
                continue
            accepted[source] = result
    if errors:
        data = {"approved": 0, "blocked": len(errors), "errors": errors,
                "changes_production_catalogue": False}
    else:
        data = {
            "approved": len(accepted), "blocked": 0,
            "changes_production_catalogue": approve and bool(accepted),
        }
        if approve:
            for source, result in accepted.items():
                original.append(polib.POEntry(
                    msgid=source, msgstr=result,
                    comment="Human-reviewed Vietnamese localization",
                ))
            if accepted:
                original.save(str(catalogue))
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(data, ensure_ascii=False, indent=2),
                           encoding="utf-8")
    print(json.dumps(data, ensure_ascii=False, indent=2))
    return 2 if errors else 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--queue", type=Path, required=True)
    parser.add_argument("--catalogue", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("--apply", action="store_true", default=False)
    args = parser.parse_args()
    raise SystemExit(apply(
        args.queue, args.catalogue, approve=args.apply, report_path=args.report
    ))

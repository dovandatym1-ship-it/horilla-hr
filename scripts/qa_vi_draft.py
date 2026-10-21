#!/usr/bin/env python3
"""Prioritize and sanity-check machine-translated HRM UI suggestions.

The output is a review CSV, not a file merged or deployed to production.
Per-message exact glossary consistency and format preservation are checked.
"""
from __future__ import annotations

import argparse
import csv
import json
import re
from collections import Counter
from pathlib import Path

# Expected terminology in HRM UI. Only whole source words are matched.
# Some polysemous source terms (leave, shift, asset) are intentionally strict.
TERMS = {
    r"\battendance\b": r"chấm công",
    r"\bpayslip(?:s)?\b": r"phiếu lương",
    r"\bpayroll\b": r"lương",
    r"\bemploye(?:e|es)\b": r"nhân viên",
    r"\bcandidate(?:s)?\b": r"ứng viên",
    r"\brecruitment\b": r"tuyển dụng",
    r"\bcontract(?:s)?\b": r"hợp đồng",
    r"\bdepartment(?:s)?\b": r"phòng ban",
    r"\bovertime\b": r"(?:làm thêm|tăng ca|OT)",
    r"\bdeduction(?:s)?\b": r"khấu trừ",
    r"\basset(?:s)?\b": r"tài sản",
    r"\bsalary\b": r"lương",
    r"\bwage(?:s)?\b": r"lương",
    r"\b(tax|taxes)\b": r"thuế",
    r"\binsurance\b": r"bảo hiểm",
    r"\breimbursement\b": r"hoàn",
    r"\b(onboarding)\b": r"(?:tiếp nhận|hội nhập)",
    r"\b(offboarding)\b": r"(?:nghỉ việc|thôi việc)",
}
# These are observed errors of early en->vi MT drafts, NOT acceptable release copy.
BAD_VI = (
    "thô tục", "lên boong", "khúc xạ", "nhịn nhục", "ban nhạc",
    "các đĩa thu", "số người tham dự", "độ thăng bằng",
    "bộ phân vùng", "bỏ đi", "ngày tận thế", "nhớ tạm",
)
PYTHON_PLACEHOLDER = re.compile(
    r"%\([a-zA-Z_][a-zA-Z_0-9]*\)[#0 +.-]*[a-zA-Z]|"
    r"%(?:\d+\$)?[sdfr]|\{[a-zA-Z_][a-zA-Z_0-9]*\}"
)
TECH_KEY = re.compile(r"^[a-z][a-z0-9_-]{3,}$")
VI_DIACRITIC = re.compile(r"[À-ỹĐđ]")


def review_one(source, translated):
    reasons = []
    if sorted(PYTHON_PLACEHOLDER.findall(source)) != sorted(
        PYTHON_PLACEHOLDER.findall(translated)
    ):
        reasons.append("format_placeholder_mismatch")
    if not translated.strip() or translated.casefold() == source.casefold():
        reasons.append("untranslated_or_identical")
    if TECH_KEY.fullmatch(source) and ("_" in source or "-" in source):
        reasons.append("technical_identifier_should_remain_untranslated")
    if not VI_DIACRITIC.search(translated) and re.search("[A-Za-z]{3}", source):
        reasons.append("no_vietnamese_diacritic")
    for en_pattern, vi_pattern in TERMS.items():
        if re.search(en_pattern, source, re.I) and not re.search(
            vi_pattern, translated, re.I
        ):
            reasons.append("missing_hrm_term:" + en_pattern)
    for unsafe in BAD_VI:
        if unsafe in translated.casefold():
            reasons.append("observed_mt_error:" + unsafe)
    # Keep copied sample names/other proper nouns for human judgment.
    if source.istitle() and len(source.split()) <= 3:
        reasons.append("short_title_requires_context")
    return sorted(set(reasons))


def review(*, source, out):
    import polib

    catalog = polib.pofile(str(source))
    rows = []
    for entry in catalog:
        if "fuzzy" not in entry.flags or not entry.msgid:
            continue
        reasons = review_one(entry.msgid, entry.msgstr)
        rows.append({
            "priority": "HIGH" if reasons else "REVIEW",
            "source": entry.msgid,
            "suggestion": entry.msgstr,
            "flags": "; ".join(reasons),
            "decision": "",  # reviewer fills APPROVE / REWRITE / REJECT
            "approved_vietnamese": "",
            "reviewer": "",
        })
    rows.sort(key=lambda d: (d["priority"] != "HIGH", d["source"].casefold()))
    out.mkdir(parents=True, exist_ok=True)
    with (out / "review_queue.csv").open("w", newline="", encoding="utf-8-sig") as file:
        writer = csv.DictWriter(file, fieldnames=list(rows[0]) if rows else [
            "priority", "source", "suggestion", "flags", "decision",
            "approved_vietnamese", "reviewer",
        ])
        writer.writeheader()
        writer.writerows(rows)
    by_flag = Counter(
        item for row in rows for item in row["flags"].split("; ") if item
    )
    report = {
        "machine_draft_total": len(rows),
        "requires_manual_review": len(rows),
        "high_priority": sum(row["priority"] == "HIGH" for row in rows),
        "quality_flags": dict(by_flag.most_common()),
        "auto_approved": 0,
        "changes_production_catalogue": False,
    }
    (out / "quality_report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    review(source=args.source, out=args.out)

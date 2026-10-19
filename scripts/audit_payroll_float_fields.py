#!/usr/bin/env python3
"""Read-only inventory of monetary FloatFields in Horilla payroll models.

NO schema change. Each field needs an explicit conversion migration, arithmetic
review, historical data audit, rollback, and regression tests before go-live.
"""
import ast
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MODELS = ROOT / "payroll" / "models" / "models.py"
MONEY_NAME = re.compile(
    r"(wage|salary|pay|cost|amount|deduct|tax|ctc|loan|"
    r"insurance|contribution|commission|reimburs|earning|gross|net)",
    re.IGNORECASE,
)
NON_MONETARY_NAME = re.compile(
    r"(percentage|percent|rate_percent|interest_rate|ratio|hours|days)",
    re.IGNORECASE,
)


def main():
    tree = ast.parse(MODELS.read_text(encoding="utf-8"), filename=str(MODELS))
    fields = []
    for item in tree.body:
        if not isinstance(item, ast.ClassDef):
            continue
        for node in item.body:
            if not isinstance(node, ast.Assign) or not isinstance(node.value, ast.Call):
                continue
            call = node.value.func
            if not isinstance(call, ast.Attribute) or call.attr != "FloatField":
                continue
            for target in node.targets:
                if not isinstance(target, ast.Name):
                    continue
                name = target.id
                if MONEY_NAME.search(name):
                    category = (
                        "possible_rate_not_money"
                        if NON_MONETARY_NAME.search(name)
                        else "monetary_conversion_candidate"
                    )
                else:
                    category = "other_float"
                fields.append({
                    "model": item.name,
                    "field": name,
                    "line": node.lineno,
                    "category": category,
                })
    candidates = [f for f in fields if f["category"] == "monetary_conversion_candidate"]
    print(json.dumps({
        "source": str(MODELS.relative_to(ROOT)),
        "all_float_fields": len(fields),
        "monetary_candidates": len(candidates),
        "fields": fields,
        "conversion_complete": False,
        "warning": (
            "Heuristic names only. Legacy engine continues to calculate with "
            "binary floats. An exact Decimal preview layer is not a replacement "
            "for model/DB conversions, rounding review, historical reconciliation."
        ),
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

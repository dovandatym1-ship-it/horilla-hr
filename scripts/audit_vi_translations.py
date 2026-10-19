#!/usr/bin/env python3
"""Audit Vietnamese gettext catalogs. Exit nonzero on missing or incomplete catalogs."""
import ast
import json
import re
import sys
from pathlib import Path

TOKEN = re.compile(r'%(?:\([^)]+\))?[-+#0 ]*\d*(?:\.\d+)?[diouxXeEfFgGcrs]|\{[a-zA-Z_][\w.]*(?:![rsa])?(?::[^{}]+)?\}')

def entries(path):
    current, field = {}, None
    for number, raw in enumerate(path.read_text(encoding="utf-8-sig").splitlines(), 1):
        line = raw.strip()
        if not line:
            if current.get("msgid"):
                yield current
            current, field = {}, None
        elif line.startswith("#~"):
            continue
        elif line.startswith("#,"):
            current["fuzzy"] = current.get("fuzzy", False) or "fuzzy" in line
        elif line.startswith(("msgid ", "msgid_plural ", "msgstr ", "msgstr[")):
            if line.startswith("msgid ") and "msgid" in current:
                if current["msgid"]:
                    yield current
                current = {}
            field, value = line.split(" ", 1)
            current[field] = ast.literal_eval(value)
            current.setdefault("line", number)
        elif line.startswith('"') and field:
            current[field] += ast.literal_eval(line)
    if current.get("msgid"):
        yield current

def main():
    root = Path(sys.argv[1] if len(sys.argv) > 1 else ".").resolve()
    catalogs = sorted(p for p in root.rglob("*.po") if any(part.lower().replace("-", "_").startswith("vi") for part in p.parts) and ".git" not in p.parts)
    errors, total = [], 0
    for path in catalogs:
        try:
            items = list(entries(path))
        except (OSError, SyntaxError, ValueError) as ex:
            errors.append({"file": str(path.relative_to(root)), "problem": "invalid_catalog", "detail": str(ex)})
            continue
        for item in items:
            total += 1
            translations = [value for key, value in item.items() if key == "msgstr" or key.startswith("msgstr[")]
            problems = []
            if item.get("fuzzy"):
                problems.append("fuzzy")
            if not translations or any(not value.strip() for value in translations):
                problems.append("untranslated")
            original_tokens = set(TOKEN.findall(item["msgid"]))
            if any(value and set(TOKEN.findall(value)) != original_tokens for value in translations):
                problems.append("placeholder_mismatch")
            for problem in problems:
                errors.append({"file": str(path.relative_to(root)), "line": item["line"], "problem": problem, "msgid": item["msgid"][:120]})
    result = {"catalogs": len(catalogs), "entries_checked": total, "issues": len(errors), "details": errors}
    print(json.dumps(result, ensure_ascii=False, indent=2))
    if not catalogs:
        print("No Vietnamese .po catalogs found; cannot certify localization.", file=sys.stderr)
        return 2
    return 1 if errors else 0

if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Read-only estimate of Django/JS Vietnamese gettext completion.

This does NOT claim 100% application UI coverage: hard-coded template strings,
PDF, spreadsheet, email and dynamic JS labels require a separate inventory.
"""
from pathlib import Path
import ast
import json
import re

ROOT = Path(__file__).resolve().parents[1]
LOCALE = ROOT / "horilla" / "locale" / "vi" / "LC_MESSAGES"


def audit_catalogue(path):
    text = path.read_text(encoding="utf-8")
    entries = []
    current = None
    field = None
    for line in text.splitlines():
        if line.startswith("msgid "):
            if current is not None:
                entries.append(current)
            current = {"msgid": "", "msgstr": ""}
            field = "msgid"
        elif line.startswith("msgstr ") and current is not None:
            field = "msgstr"
        elif not line.startswith('"'):
            field = None
            continue
        if field and current is not None:
            match = re.match(r'^(?:msgid |msgstr )?(".*")$', line)
            if match:
                try:
                    current[field] += ast.literal_eval(match.group(1))
                except (SyntaxError, ValueError):
                    pass
    if current is not None:
        entries.append(current)
    messages = [x for x in entries if x["msgid"]]
    return {
        "total": len(messages),
        "translated": sum(bool(x["msgstr"]) for x in messages),
        "empty": sum(not x["msgstr"] for x in messages),
    }


def main():
    catalogues = {}
    for file in ("django.po", "djangojs.po"):
        path = LOCALE / file
        catalogues[file] = audit_catalogue(path) if path.exists() else {
            "total": 0, "translated": 0, "empty": 0, "missing": True
        }
    print(json.dumps({
        "catalogues": catalogues,
        "warning": (
            "Gettext-only audit; excludes untranslated template literals, "
            "runtime JS, emails, exports, PDF and accessibility strings."
        ),
        "ready_for_100_percent_claim": False,
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

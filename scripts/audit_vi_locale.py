#!/usr/bin/env python3
"""Audit Vietnamese gettext coverage AND probable English UI literals.

This is a source-code inventory, not a certification of 100% translation.
Runtime-generated strings, rich exports and human UX sign-off still need review.
Run: python scripts/audit_vi_locale.py
"""
from __future__ import annotations

import ast
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LOCALE = ROOT / "horilla" / "locale" / "vi" / "LC_MESSAGES"
SKIP_PARTS = frozenset(
    ("migrations", "tests", "node_modules", "vendor", "vendors", "cdn",
     "build", "dist", "locale", ".git", "staticfiles", "media")
)
SOURCE_EXTENSIONS = frozenset((".html", ".py", ".js"))
DJANGO_TAG = re.compile(r"""\{%\s*(?:trans|translate)\s+(['"])(.*?)\1""")
PYTHON_GETTEXT = re.compile(
    r"""(?<!\w)(?:_|gettext|gettext_lazy|gettext_noop|ugettext|ugettext_lazy)\(\s*(['"])(.*?)\1"""
)
JS_GETTEXT = re.compile(r"""\bgettext\(\s*(['"])(.*?)\1""")
VISIBLE_TEXT = re.compile(r">\s*([^<>\n]{3,180}?)\s*<")
VISIBLE_ATTR = re.compile(
    r"""\b(?:placeholder|title|aria-label|alt)\s*=\s*(['"])(.*?)\1"""
)
LATIN = re.compile(r"[A-Za-z]{3,}")
VI_DIACRITICS = re.compile(r"[À-ỹĐđ]")
HARD_CODED_EN_LANG = re.compile(r"""<html\b[^>]*\blang\s*=\s*['"]en['"]""", re.I)
JS_DIALOG = re.compile(
    r"""\b(?:alert|confirm|prompt)\(\s*(['"])([^'"]{3,160})\1""",
    re.I,
)



def catalogue_entries(path):
    """Parse the usual msgid/msgstr pairs and continuation lines without deps.

    Plural/context entries require a separate gettext-level audit: this
    deliberately reports only messages that can be verified by this parser.
    """
    entries = []
    current = None
    field = None
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.startswith("msgid "):
            if current is not None:
                entries.append(current)
            current = {"msgid": "", "msgstr": ""}
            field = "msgid"
        elif line.startswith("msgstr ") and current is not None:
            field = "msgstr"
        elif line.startswith(("msgctxt ", "msgid_plural ", "msgstr[")):
            field = None
        elif not line.startswith('"'):
            field = None
            continue
        if current is None or field is None:
            continue
        literal = re.match(r'^(?:msgid |msgstr )?(".*")$', line)
        if literal:
            try:
                current[field] += ast.literal_eval(literal.group(1))
            except (ValueError, SyntaxError):
                field = None
    if current is not None:
        entries.append(current)
    return [entry for entry in entries if entry["msgid"]]


def source_files():
    for path in ROOT.rglob("*"):
        if not path.is_file() or path.suffix not in SOURCE_EXTENSIONS:
            continue
        if set(path.relative_to(ROOT).parts) & SKIP_PARTS:
            continue
        if path.name.endswith((".min.js", ".bundle.js")):
            continue
        if path.stat().st_size > 300_000:
            continue
        yield path


def visible_candidates(contents):
    """Find likely untranslated English copy, excluding icon glyphs and VI.

    This is a heuristic; only real UI tests establish screen-level coverage.
    """
    contents = re.sub(
        r"{%\s*comment\s*%}.*?{%\s*endcomment\s*%}",
        "", contents, flags=re.S,
    )
    contents = re.sub(
        r"<!--.*?-->|<script\b.*?</script>|<style\b.*?</style>",
        "", contents, flags=re.S | re.I,
    )

    def looks_like_english_copy(value):
        if not LATIN.search(value) or any(c in value for c in ("{", "}", "$")):
            return False
        if VI_DIACRITICS.search(value):
            return False
        if re.fullmatch(r"(?:&[a-zA-Z]+;?|[.,;:()\s])+", value):
            return False
        if re.fullmatch(r"[a-z][a-z0-9_-]*", value) and (
            "_" in value or "-" in value
        ):
            return False
        if value in ("Email", "CSV", "API", "CTC", "HRM", "OT",
                     "John Doe", "Alice Smith", "Robert Johnson",
                     "Adam Luis", "Lizaveta Ivanovna", "Abigail Lee",
                     "Mary Magdalene", "Aliza B"):
            return False
        return True

    result = []
    for match in VISIBLE_TEXT.finditer(contents):
        value = match.group(1).strip()
        if not looks_like_english_copy(value):
            continue
        parent_tag = contents[contents.rfind("<", 0, match.start()):match.start()]
        if re.search(
            r"<(?:ion-icon|mat-icon|i|span)\b[^>]*(?:material-icons|"
            r"material-symbols|icon-font|\bicon\b)",
            parent_tag, flags=re.I,
        ):
            continue
        result.append(value)
    for match in VISIBLE_ATTR.finditer(contents):
        value = match.group(2).strip()
        if looks_like_english_copy(value):
            result.append(value)
    return result


def main():
    entries_by_catalogue = {}
    for filename in ("django.po", "djangojs.po"):
        path = LOCALE / filename
        entries_by_catalogue[filename] = catalogue_entries(path) if path.exists() else []
    catalogues = {
        name: {
            "total": len(entries),
            "translated": sum(bool(entry["msgstr"]) for entry in entries),
            "empty": sum(not entry["msgstr"] for entry in entries),
        }
        for name, entries in entries_by_catalogue.items()
    }
    django_ids = {
        x["msgid"] for x in entries_by_catalogue["django.po"] if x["msgstr"]
    }
    js_ids = {
        x["msgid"] for x in entries_by_catalogue["djangojs.po"] if x["msgstr"]
    }
    refs = {"django": set(), "djangojs": set()}
    literal_samples = []
    candidate_count = 0
    files_scanned = 0
    hardcoded_en_lang = []
    js_dialogs = []
    for path in source_files():
        try:
            content = path.read_text(encoding="utf-8")
        except (UnicodeError, OSError):
            continue
        files_scanned += 1
        relative = str(path.relative_to(ROOT))
        if path.suffix == ".html":
            if HARD_CODED_EN_LANG.search(content):
                hardcoded_en_lang.append(relative)
            for dialog in JS_DIALOG.finditer(content):
                if LATIN.search(dialog.group(2)) and not VI_DIACRITICS.search(dialog.group(2)):
                    js_dialogs.append({"file": relative, "text": dialog.group(2)})
            refs["django"].update(m.group(2) for m in DJANGO_TAG.finditer(content))
            values = visible_candidates(content)
            candidate_count += len(values)
            for value in values:
                literal_samples.append({"file": relative, "text": value[:120]})
        elif path.suffix == ".py":
            refs["django"].update(m.group(2) for m in PYTHON_GETTEXT.finditer(content))
        elif path.suffix == ".js":
            refs["djangojs"].update(m.group(2) for m in JS_GETTEXT.finditer(content))
            for dialog in JS_DIALOG.finditer(content):
                if LATIN.search(dialog.group(2)) and not VI_DIACRITICS.search(dialog.group(2)):
                    js_dialogs.append({"file": relative, "text": dialog.group(2)})

    missing_django = sorted(refs["django"] - django_ids)
    missing_js = sorted(refs["djangojs"] - js_ids)
    total_references = len(refs["django"]) + len(refs["djangojs"])
    translated_references = (
        len(refs["django"] & django_ids) + len(refs["djangojs"] & js_ids)
    )
    # Distinct gettext keys, not rendered-string or screen-level coverage.
    gettext_coverage_pct = (
        round(translated_references * 100 / total_references, 2)
        if total_references else 100.0
    )
    print(json.dumps({
        "catalogues": catalogues,
        "scanned_source_files": files_scanned,
        "gettext_references": {
            "django": len(refs["django"]),
            "djangojs": len(refs["djangojs"]),
        },
        "missing_gettext_keys": {
            "django": len(missing_django),
            "djangojs": len(missing_js),
        },
        "gettext_coverage": {
            "distinct_required": total_references,
            "distinct_translated": translated_references,
            "percentage": gettext_coverage_pct,
            "metric_scope": "statically_detectable_simple_gettext_keys_only",
        },
        "missing_examples": {
            "django": missing_django[:60],
            "djangojs": missing_js[:60],
        },
        "missing_all": {
            "django": missing_django,
            "djangojs": missing_js,
        },
        "hardcoded_english_html_lang_count": len(hardcoded_en_lang),
        "hardcoded_english_html_lang_files": hardcoded_en_lang,
        "unwrapped_javascript_dialog_count": len(js_dialogs),
        "unwrapped_javascript_dialog_examples": js_dialogs[:75],
        "unwrapped_html_candidates": candidate_count,
        "unwrapped_html_examples": literal_samples[:60],
        "unwrapped_html_all": literal_samples,
        "ready_for_100_percent_claim": False,
        "warning": (
            "Approximate static audit only. Contextual/plural gettext, dynamically "
            "built JS, unwrapped strings, emails, PDF, Excel, responsive screens "
            "and human UAT must be separately verified."
        ),
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

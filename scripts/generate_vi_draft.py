#!/usr/bin/env python3
"""Produce a separately-reviewable Vietnamese gettext machine-translation draft.

The source .po files are NEVER modified. No generated string enters production
without manual approval. The open-source en->vi model runs locally on the CI
worker after weights are downloaded (no translation API or runtime network).
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.audit_vi_locale import DJANGO_TAG, PYTHON_GETTEXT, source_files

MARIAN_MODEL_ID = "Helsinki-NLP/opus-mt-en-vi"
ENVIT5_MODEL_ID = "VietAI/envit5-translation"
MODEL_ID = MARIAN_MODEL_ID
PLACEHOLDER = re.compile(
    r"(%\([a-zA-Z_][a-zA-Z_0-9]*\)[#0 +.-]*[a-zA-Z]|"
    r"%(?:\d+\$)?[sdfr]|"
    r"\{(?:[a-zA-Z_][a-zA-Z_0-9]*|\d*)\}|"
    r"<[^<>]*>|"
    r"\{\{[^{}]*\}\}|\{%[^%]*%\})"
)
ENGLISH = re.compile(r"[A-Za-z]{2,}")
VI_DIACRITIC = re.compile(r"[À-ỹĐđ]")


def source_keys():
    keys = set()
    for path in source_files():
        if path.suffix not in (".html", ".py"):
            continue
        try:
            contents = path.read_text(encoding="utf-8")
        except (UnicodeError, OSError):
            continue
        pattern = DJANGO_TAG if path.suffix == ".html" else PYTHON_GETTEXT
        keys.update(match.group(2) for match in pattern.finditer(contents))
    return keys - {""}


def pieces_for(source):
    """Protect all interpolation placeholders and tags by never sending them to MT."""
    return PLACEHOLDER.split(source)


def safe_text(text):
    """No guessing for source code, numbers, empty input, or oversized sentences."""
    body = text.strip()
    if len(body) < 2 or len(body) > 350 or not ENGLISH.search(body):
        return False
    if re.match(r"^(?:https?://|[\w.-]+@[\w.-]+)", body):
        return False
    if not re.search(r"[A-Za-z]{2,}", body):
        return False
    return True


def build_translation_requests(keys, existing):
    requests = set()
    key_parts = {}
    excluded = {}
    for key in sorted(keys):
        if key in existing:
            continue
        parts = pieces_for(key)
        if len(parts) > 100:
            excluded[key] = "too_many_interpolations"
            continue
        pending = []
        for index, fragment in enumerate(parts):
            if index % 2:
                continue  # protected interpolation/markup
            if safe_text(fragment) and fragment.strip() not in existing:
                pending.append(fragment.strip())
        if len(key) > 1200:
            excluded[key] = "oversized_message"
            continue
        key_parts[key] = parts
        requests.update(pending)
    return key_parts, sorted(requests), excluded


def model_translations(texts, *, batch_size, model_id=MODEL_ID):
    """Batch CPU translation; translated fragments contain no protected tokens."""
    if not texts:
        return {}
    import torch
    from transformers import AutoModelForSeq2SeqLM, AutoTokenizer

    torch.set_num_threads(2)
    tokenizer = AutoTokenizer.from_pretrained(model_id)
    model = AutoModelForSeq2SeqLM.from_pretrained(model_id)
    model.eval()
    results = {}
    for offset in range(0, len(texts), batch_size):
        batch = texts[offset:offset + batch_size]
        # EnViT5 requires en: input and returns vi: output, whereas Marian
        # requires the translation language marker in its source text.
        prefixed = [("en: " if model_id == ENVIT5_MODEL_ID else ">>vie<< ") + item
                    for item in batch]
        inputs = tokenizer(prefixed, padding=True, truncation=True,
                           max_length=192, return_tensors="pt")
        with torch.inference_mode():
            output = model.generate(
                **inputs, max_new_tokens=128, num_beams=2,
                early_stopping=True,
            )
        translated = tokenizer.batch_decode(output, skip_special_tokens=True)
        for source, target in zip(batch, translated):
            target = target.strip()
            if model_id == ENVIT5_MODEL_ID and target.startswith("vi:"):
                target = target[3:].strip()
            results[source] = target
        if (offset // batch_size) % 15 == 0:
            print(f"Translated {min(offset + batch_size, len(texts))}/{len(texts)} fragments", flush=True)
    return results


def build_draft(*, target, batch_size, model_id=MODEL_ID):
    import polib

    original_path = ROOT / "horilla/locale/vi/LC_MESSAGES/django.po"
    original = polib.pofile(str(original_path))
    existing = {entry.msgid: entry.msgstr for entry in original
                if entry.msgid and entry.msgstr and "fuzzy" not in entry.flags}
    key_parts, requests, excluded = build_translation_requests(source_keys(), existing)
    translations = model_translations(requests, batch_size=batch_size, model_id=model_id)
    created = []
    rejected = {}
    for key, parts in key_parts.items():
        translated_parts = []
        for index, fragment in enumerate(parts):
            if index % 2:
                translated_parts.append(fragment)
                continue
            body = fragment.strip()
            if not safe_text(fragment):
                translated_parts.append(fragment)
                continue
            translation = existing.get(body) or translations.get(body)
            if not translation or translation.casefold() == body.casefold():
                rejected[key] = "missing_or_unchanged_translation"
                break
            left = fragment[:len(fragment) - len(fragment.lstrip())]
            right = fragment[len(fragment.rstrip()):]
            translated_parts.append(left + translation + right)
        else:
            value = "".join(translated_parts)
            if sorted(PLACEHOLDER.findall(value)) != sorted(PLACEHOLDER.findall(key)):
                rejected[key] = "interpolation_not_preserved"
                continue
            if not VI_DIACRITIC.search(value) and ENGLISH.search(key):
                rejected[key] = "not_recognizably_vietnamese"
                continue
            # A fuzzy draft entry is never compiled into production by msgfmt.
            original.append(polib.POEntry(
                msgid=key, msgstr=value,
                comment="MACHINE TRANSLATION DRAFT — review HRM domain terminology",
                flags=["fuzzy"],
            ))
            created.append(key)
    target.mkdir(parents=True, exist_ok=True)
    draft = target / "django.draft.po"
    original.save(str(draft))
    report = {
        "input_source": "simple Django gettext extraction",
        "model": model_id,
        "translated_draft_count": len(created),
        "rejected_count": len(rejected),
        "excluded_count": len(excluded),
        "already_approved_count": len(existing),
        "draft_is_fuzzy_not_for_runtime": True,
        "draft_path": draft.name,
        "rejection_reasons": dict(Counter(rejected.values())),
        "exclusion_reasons": dict(Counter(excluded.values())),
        "rejected_keys_sample": list(rejected)[:100],
        "excluded_keys_sample": list(excluded)[:100],
        "requires_human_review": True,
    }
    (target / "review_report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(json.dumps({
        k: v for k, v in report.items()
        if k not in ("rejected_keys_sample", "excluded_keys_sample")
    }, ensure_ascii=False, indent=2))
    return 0 if created else 2


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--batch-size", type=int, default=16)
    parser.add_argument("--model-id", choices=(MARIAN_MODEL_ID, ENVIT5_MODEL_ID),
                        default=MARIAN_MODEL_ID)
    args = parser.parse_args()
    if not 1 <= args.batch_size <= 64:
        parser.error("--batch-size must be between 1 and 64")
    raise SystemExit(build_draft(target=args.out, batch_size=args.batch_size,
                                 model_id=args.model_id))

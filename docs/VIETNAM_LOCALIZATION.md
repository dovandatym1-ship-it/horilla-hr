# Vietnamese localization: first executable slice

This branch introduces **runtime code**, unlike the documentation-only planning PR.

## Changes in this slice
- Vietnamese is the default interface language (`LANGUAGE_CODE=vi`), with English and existing locales still selectable if enabled by the company.
- Default timezone becomes `Asia/Ho_Chi_Minh` and the newly created payroll currency symbol defaults to `₫`.
- Adds locale-specific date and number formats; `17/10/2026`, `1.234.567,89`.
- Adds gettext catalogs for key human resources, attendance, leave, payroll and interface strings. Untranslated keys still show English; **this is not 100% coverage**.
- Includes regression tests for locale formats, language preference and new-vs-existing payroll currency settings.

## Deploy
```bash
git checkout feature/vn-i18n-foundation
docker compose up --build -d
```
The Dockerfile already compiles `.po` catalogs to `.mo` via `msgfmt`. Development Compose bind-mounts source code, and its entrypoint compiles missing catalogs. Manual development without Docker needs **GNU gettext** and:
```bash
python manage.py compilemessages -l vi
python manage.py runserver
```

Override locale without editing source:
```dotenv
LANGUAGE_CODE=vi
TIME_ZONE=Asia/Ho_Chi_Minh
DEFAULT_CURRENCY_SYMBOL=₫
```

Existing `PayrollSettings` rows and users' explicit session currency preferences are preserved; upgrading an existing company does not silently rewrite USD/EUR settings.

## Validation
- `python manage.py check`
- `python manage.py test horilla.tests.test_vietnam_localization payroll.tests.test_vietnam_currency`
- `python manage.py makemigrations --check --dry-run`
- Confirm a new company on the UI, switch languages, verify a Vietnamese date and currency, and inspect emails/PDF/exports separately.

## Remaining code work
Core UX translations beyond the curated first catalog, custom JS strings, company-specific date configuration, employee legal identity data, employment contracts, attendance/OT policies, leave rules and statutory payroll are **not yet implemented**. Never use this slice as proof of Vietnamese payroll compliance. See the business analysis in PR #1 (docs/vietnam).

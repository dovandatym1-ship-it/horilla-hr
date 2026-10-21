"""Default-currency regression tests for newly created payroll settings."""

from types import SimpleNamespace
from unittest.mock import patch

from django.test import SimpleTestCase, override_settings

from payroll.context_processors import default_currency


class VietnameseCurrencyTests(SimpleTestCase):
    def test_new_company_uses_configured_vietnamese_currency(self):
        request = SimpleNamespace(
            session={},
            selected_company_instance=None,
        )
        with (
            override_settings(DEFAULT_CURRENCY_SYMBOL="₫"),
            patch("payroll.context_processors.models.PayrollSettings.objects.first", return_value=None),
            patch("payroll.context_processors.models.PayrollSettings.save") as save,
        ):
            result = default_currency(request)
            self.assertEqual(result["currency"], "₫")
            save.assert_called_once()

    def test_existing_company_currency_is_never_overwritten(self):
        request = SimpleNamespace(session={})
        payroll_setting = SimpleNamespace(currency_symbol="€", position="prefix")
        with patch(
            "payroll.context_processors.models.PayrollSettings.objects.first",
            return_value=payroll_setting,
        ):
            self.assertEqual(default_currency(request), {"currency": "€", "position": "prefix"})

    def test_explicit_session_preference_is_kept(self):
        request = SimpleNamespace(session={"currency": "$", "position": "prefix"})
        payroll_setting = SimpleNamespace(currency_symbol="₫", position="postfix")
        with patch(
            "payroll.context_processors.models.PayrollSettings.objects.first",
            return_value=payroll_setting,
        ):
            self.assertEqual(default_currency(request), {"currency": "$", "position": "prefix"})

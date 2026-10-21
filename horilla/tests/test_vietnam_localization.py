"""Regression tests for Vietnamese-first, opt-out-capable locale configuration."""

from datetime import date
from decimal import Decimal
from unittest.mock import patch

from django.conf import settings
from django.test import SimpleTestCase, override_settings
from django.utils import formats, translation
from django.utils.formats import date_format, number_format

from horilla.horilla_middlewares import DefaultLanguageMiddleware


class VietnameseLocalizationTests(SimpleTestCase):
    def test_vietnamese_is_selectable(self):
        self.assertIn("vi", dict(settings.LANGUAGES))
        self.assertEqual(settings.FORMAT_MODULE_PATH, ["horilla.vietnam_formats"])

    def test_vietnamese_date_and_time_formats(self):
        with translation.override("vi"):
            self.assertEqual(formats.get_format("DATE_FORMAT"), "d/m/Y")
            self.assertEqual(formats.get_format("DATETIME_FORMAT"), "d/m/Y H:i")
            self.assertEqual(date_format(date(2026, 10, 17)), "17/10/2026")

    def test_vietnamese_decimal_separators(self):
        with translation.override("vi"):
            self.assertEqual(formats.get_format("DECIMAL_SEPARATOR"), ",")
            self.assertEqual(formats.get_format("THOUSAND_SEPARATOR"), ".")
            self.assertEqual(
                number_format(Decimal("1234567.89"), force_grouping=True),
                "1.234.567,89",
            )

    def test_english_format_not_overridden(self):
        with translation.override("en"):
            self.assertNotEqual(formats.get_format("THOUSAND_SEPARATOR"), ".")

    def test_explicit_language_cookie_takes_priority(self):
        class Request:
            COOKIES = {settings.LANGUAGE_COOKIE_NAME: "en"}
            META = {"HTTP_ACCEPT_LANGUAGE": "fr"}

        request = Request()
        middleware = DefaultLanguageMiddleware(lambda r: r)
        middleware(request)
        self.assertEqual(request.META["HTTP_ACCEPT_LANGUAGE"], "fr")

    def test_browser_language_does_not_override_default(self):
        class Request:
            COOKIES = {}
            META = {"HTTP_ACCEPT_LANGUAGE": "en"}

        request = Request()
        middleware = DefaultLanguageMiddleware(lambda r: r)
        middleware(request)
        self.assertNotIn("HTTP_ACCEPT_LANGUAGE", request.META)

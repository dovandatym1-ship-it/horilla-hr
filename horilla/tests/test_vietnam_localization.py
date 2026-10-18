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


class VietnameseCatalogueIntegrityTests(SimpleTestCase):
    """Regression gate for critical Vietnamese copy in both gettext catalogues."""

    @staticmethod
    def _translations(catalogue):
        import ast
        from pathlib import Path
        import re

        root = Path(__file__).resolve().parents[2]
        path = root / "horilla" / "locale" / "vi" / "LC_MESSAGES" / catalogue
        raw = path.read_text(encoding="utf-8")
        pairs = re.findall(
            r'^msgid (".*")\nmsgstr (".*")$', raw, flags=re.MULTILINE
        )
        result = {}
        for source, translation in pairs:
            key = ast.literal_eval(source)
            value = ast.literal_eval(translation)
            if not key:
                continue
            if key in result:
                raise AssertionError(f"Duplicate msgid in {catalogue}: {key}")
            result[key] = value
        return result

    def test_django_core_hrm_and_payslip_translations(self):
        catalogue = self._translations("django.po")
        self.assertGreaterEqual(len(catalogue), 590)
        self.assertEqual(catalogue["Sign In"], "Đăng nhập")
        self.assertEqual(catalogue["Payslip"], "Phiếu lương")
        self.assertEqual(catalogue["Social Insurance"], "Bảo hiểm xã hội")
        self.assertEqual(catalogue["Contract Amendment"], "Phụ lục hợp đồng")
        self.assertEqual(
            catalogue["Status not updated."], "Chưa cập nhật được trạng thái."
        )

    def test_javascript_dialog_translations(self):
        catalogue = self._translations("djangojs.po")
        self.assertGreaterEqual(len(catalogue), 110)
        self.assertEqual(catalogue["Confirm"], "Xác nhận")
        self.assertEqual(catalogue["Cancel"], "Hủy")
        self.assertEqual(
            catalogue["Do you want to send the payslip by mail?"],
            "Bạn có muốn gửi phiếu lương qua email không?",
        )

    def test_source_templates_do_not_hardcode_critical_english(self):
        from pathlib import Path

        root = Path(__file__).resolve().parents[2]
        navbar = (root / "templates" / "navbar.html").read_text(encoding="utf-8")
        payslips = (
            root / "payroll" / "templates" / "payroll" / "payslip"
            / "view_payslips.html"
        ).read_text(encoding="utf-8")
        self.assertIn('{% trans "Mark as read" %}', navbar)
        self.assertIn("{% trans 'Status not updated.' %}", payslips)
        self.assertNotIn(">My Profile</a>", navbar)
        self.assertNotIn(">Log out</a>", navbar)

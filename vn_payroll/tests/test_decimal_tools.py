"""Independent numerical scenarios; figures are TEST FIXTURES, not VN law."""

from decimal import Decimal

from django.core.exceptions import ValidationError
from django.test import SimpleTestCase

from vn_payroll.decimal_tools import as_decimal, percentage, vnd


class VietnamDecimalBoundaryTests(SimpleTestCase):
    def test_decimal_conversion_exact_from_string(self):
        self.assertEqual(as_decimal("0.1") + as_decimal("0.2"), Decimal("0.3"))

    def test_vnd_rounds_half_up(self):
        self.assertEqual(vnd("100.5"), Decimal("101"))
        self.assertEqual(vnd("100.49"), Decimal("100"))

    def test_percentage_from_policy_and_cap(self):
        self.assertEqual(
            percentage(base="25000000", rate_percent="8", ceiling="20000000"),
            Decimal("1600000"),
        )

    def test_zero_rate_and_zero_base(self):
        self.assertEqual(percentage(base="0", rate_percent="0"), Decimal("0"))

    def test_reject_nonfinite_bool_and_invalid_policy(self):
        for value in (True, None, "NaN", "Infinity", float("inf")):
            with self.subTest(value=str(value)), self.assertRaises(ValidationError):
                as_decimal(value)
        with self.assertRaises(ValidationError):
            percentage(base="100", rate_percent="-1")
        with self.assertRaises(ValidationError):
            percentage(base="100", rate_percent="101")
        with self.assertRaises(ValidationError):
            percentage(base="100", rate_percent="8", ceiling="-1")

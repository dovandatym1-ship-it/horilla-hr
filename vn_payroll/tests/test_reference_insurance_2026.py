"""Independent reference vectors for a standard covered VN employee in 2026."""
from datetime import date
from decimal import Decimal

from django.core.exceptions import ValidationError
from django.test import SimpleTestCase

from vn_payroll.reference_insurance_2026 import standard_contributions_2026


class Insurance2026ReferenceTests(SimpleTestCase):
    def invoke(self, **overrides):
        values = {
            "effective_on": date(2026, 10, 18),
            "vietnamese_standard_employee": True,
            "social_base": "20000000",
            "health_base": "20000000",
            "unemployment_base": "20000000",
        }
        return standard_contributions_2026(**(values | overrides))

    def test_standard_amounts(self):
        result = self.invoke()
        self.assertEqual(result["employee_total_vnd"], Decimal("2100000"))
        self.assertEqual(result["employer_total_vnd"], Decimal("4300000"))
        self.assertEqual(result["employee"]["employee_social"], Decimal("1600000"))
        self.assertEqual(result["employer"]["employer_occupational"], Decimal("100000"))

    def test_separate_bases(self):
        result = self.invoke(health_base="10000000", unemployment_base="15000000")
        self.assertEqual(result["employee_total_vnd"], Decimal("1900000"))
        self.assertEqual(result["employer_total_vnd"], Decimal("4000000"))

    def test_reject_unverified_worker_and_bases(self):
        cases = (
            {"vietnamese_standard_employee": False},
            {"effective_on": date(2027, 1, 1)},
            {"social_base": "-1"},
            {"health_base": "nan"},
            {"unemployment_base": None},
        )
        for kwargs in cases:
            with self.subTest(kwargs=kwargs), self.assertRaises(ValidationError):
                self.invoke(**kwargs)

"""Golden vectors independently recomputed from 2026 resident tax bands.

Rates are for full-year 2026 salary tax; not employment/coverage decisions.
"""
from decimal import Decimal

from django.core.exceptions import ValidationError
from django.test import SimpleTestCase

from vn_payroll.reference_pit_2026 import resident_monthly_salary_pit


class ResidentPIT2026Test(SimpleTestCase):
    def test_income_below_allowance(self):
        value = resident_monthly_salary_pit(
            tax_year=2026, taxable_salary_before_deductions="15500000",
            compulsory_insurance="0", verified_dependents=0,
        )
        self.assertEqual(value["resident_pit_vnd"], Decimal("0"))

    def test_resident_tax_in_first_bracket(self):
        value = resident_monthly_salary_pit(
            tax_year=2026, taxable_salary_before_deductions="25500000",
            compulsory_insurance="0", verified_dependents=0,
        )
        self.assertEqual(value["taxable_base_vnd"], Decimal("10000000"))
        self.assertEqual(value["resident_pit_vnd"], Decimal("500000"))

    def test_third_bracket_and_verified_dependent(self):
        value = resident_monthly_salary_pit(
            tax_year=2026, taxable_salary_before_deductions="71700000",
            compulsory_insurance="0", verified_dependents=1,
        )
        # 71.7m - 15.5m - 6.2m = 50m; 0.5m + 2m + 4m = 6.5m
        self.assertEqual(value["taxable_base_vnd"], Decimal("50000000"))
        self.assertEqual(value["resident_pit_vnd"], Decimal("6500000"))

    def test_reject_wrong_year_and_invalid_inputs(self):
        params = {
            "tax_year": 2026, "taxable_salary_before_deductions": "20000000",
            "compulsory_insurance": "0", "verified_dependents": 0,
        }
        for change in (
            {"tax_year": 2025}, {"verified_dependents": -1},
            {"verified_dependents": "1"},
            {"taxable_salary_before_deductions": "-1"},
            {"compulsory_insurance": "NaN"},
        ):
            with self.subTest(change=change), self.assertRaises(ValidationError):
                resident_monthly_salary_pit(**(params | change))

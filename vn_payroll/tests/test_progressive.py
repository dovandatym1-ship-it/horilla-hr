from datetime import date
from decimal import Decimal

from django.core.exceptions import ValidationError
from django.test import SimpleTestCase

from vn_payroll.brackets import progressive_amount, validate_brackets
from vn_payroll.expression import InvalidFormula
from vn_payroll.models import FormulaRule


class ConfigurableProgressiveTests(SimpleTestCase):
    BRACKETS = [
        {"up_to": "10000000", "rate_percent": "5"},
        {"up_to": "30000000", "rate_percent": "10"},
        {"up_to": "60000000", "rate_percent": "20"},
        {"up_to": "100000000", "rate_percent": "30"},
        {"up_to": None, "rate_percent": "35"},
    ]

    def test_configurable_tiers_have_expected_output(self):
        # This verifies *arithmetic only*, not applicability of 2026 tax law.
        self.assertEqual(progressive_amount("35000000", self.BRACKETS), Decimal("3500000"))
        self.assertEqual(progressive_amount("0", self.BRACKETS), Decimal("0"))
        self.assertEqual(progressive_amount("-100", self.BRACKETS), Decimal("0"))

    def test_rules_can_use_editable_brackets(self):
        rule = FormulaRule(
            company_id=1,
            code="TEST_PROG",
            title="Demo progressive",
            category="tax",
            calculation_kind="progressive",
            brackets=self.BRACKETS,
            expression="",
            variables=["taxable_income"],
            effective_from=date(2026, 1, 1),
        )
        rule.clean()
        self.assertEqual(
            rule.calculate_preview({"taxable_income": "35000000"}), Decimal("3500000")
        )

    def test_rejects_unsorted_and_missing_infinity_tiers(self):
        invalid = [
            [{"up_to": "10", "rate_percent": "5"}, {"up_to": "9", "rate_percent": "10"}],
            [{"up_to": None, "rate_percent": "5"}, {"up_to": None, "rate_percent": "10"}],
            [{"up_to": "10", "rate_percent": "5"}],
            [{"up_to": None, "rate_percent": "-1"}],
            [{"up_to": None, "rate_percent": "101"}],
        ]
        for rows in invalid:
            with self.subTest(rows=rows):
                with self.assertRaises(InvalidFormula):
                    validate_brackets(rows)

    def test_status_does_not_prove_legal_compliance(self):
        rule = FormulaRule(
            company_id=1,
            code="TEST_PROG",
            title="Demo progressive",
            category="tax",
            calculation_kind="progressive",
            brackets=self.BRACKETS,
            expression="taxable_income * 0.1",
            variables=["taxable_income"],
            effective_from=date(2026, 1, 1),
        )
        with self.assertRaises(ValidationError):
            rule.clean()

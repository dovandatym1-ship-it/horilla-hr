from datetime import date
from decimal import Decimal

from django.core.exceptions import ValidationError
from django.test import SimpleTestCase

from vn_payroll.models import FormulaRule


class FormulaRuleValidationTests(SimpleTestCase):
    def make_rule(self, **kwargs):
        data = {
            "company_id": 1,
            "code": "GROSS_TO_NET",
            "version": 1,
            "title": "Thực lĩnh",
            "category": "net",
            "expression": "gross - tax",
            "variables": ["gross", "tax"],
            "effective_from": date(2026, 1, 1),
            "status": "draft",
        }
        data.update(kwargs)
        return FormulaRule(**data)

    def test_valid_formula_preview(self):
        rule = self.make_rule()
        rule.clean()
        self.assertEqual(
            rule.calculate_preview({"gross": "20000000", "tax": "1500000"}),
            Decimal("18500000"),
        )

    def test_unsupported_expression_is_rejected(self):
        rule = self.make_rule(expression="__import__('os').system('echo bad')")
        with self.assertRaises(ValidationError):
            rule.clean()

    def test_invalid_effective_period(self):
        rule = self.make_rule(effective_to=date(2025, 1, 1))
        with self.assertRaises(ValidationError):
            rule.clean()

    def test_approval_requires_audit_fields(self):
        rule = self.make_rule(status="approved")
        with self.assertRaises(ValidationError):
            rule.clean()

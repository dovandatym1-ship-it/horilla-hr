"""DB model invariants and company/effective-date rulebook behavior."""
from datetime import date
from decimal import Decimal

from django.core.exceptions import ValidationError
from django.test import TestCase

from horilla.testkit import make_company, make_user
from vn_payroll.models import VNPayRule, VNRuleSet
from vn_payroll.services import approved_ruleset_for, preview_ruleset


class VNRuleBookTests(TestCase):
    def setUp(self):
        self.company = make_company()
        self.maker = make_user("vn_rule_maker")
        self.approver = make_user("vn_rule_checker")
        self.book = VNRuleSet.objects.create(
            company=self.company, code="monthly_payroll", title="Bảng lương tùy chỉnh",
            version=1, effective_from=date(2026, 1, 1),
            legal_reference="Quy chế lương đã được duyệt nội bộ",
            parameters={"rate": "0.1"}, input_names=["salary"],
            golden_cases=[{"inputs": {"salary": "10000000"}, "expected": {"net": "9000000"}}],
            created_by=self.maker,
        )
        VNPayRule.objects.create(
            rule_set=self.book, code="gross", position=10, category="earning",
            label="Tổng thu nhập", expression="salary",
        )
        VNPayRule.objects.create(
            rule_set=self.book, code="insurance", position=20,
            category="insurance_employee", label="Khấu trừ thử",
            expression="gross * rate",
        )
        VNPayRule.objects.create(
            rule_set=self.book, code="net", position=30, category="net",
            label="Thực lĩnh thử", expression="gross - insurance",
        )

    def test_preview_does_not_write_payslips(self):
        preview = preview_ruleset(self.book, {"salary": "10000000"})
        self.assertEqual(preview["lines"][-1]["amount"], Decimal("9000000"))

    def test_client_must_not_override_approved_rate(self):
        with self.assertRaises(ValidationError):
            preview_ruleset(self.book, {"salary": "10000000", "rate": "0.99"})

    def test_approval_requires_distinct_checker(self):
        self.book.status = "review"
        self.book.save()
        with self.assertRaises(ValidationError):
            self.book.approve(self.maker)
        self.book.approve(self.approver)
        self.assertEqual(self.book.status, "approved")
        self.assertEqual(approved_ruleset_for(self.company.pk, "monthly_payroll", date(2026, 2, 1)).pk, self.book.pk)
        with self.assertRaises(ValidationError):
            preview_ruleset(VNRuleSet.objects.get(pk=self.book.pk), {"salary": "10", "rate": "2"})

    def test_approved_rules_are_immutable(self):
        self.book.status = "review"
        self.book.save()
        self.book.approve(self.approver)
        self.book.parameters = {"rate": "0.99"}
        with self.assertRaises(ValidationError):
            self.book.save()

    def test_unapproved_rules_do_not_go_to_production(self):
        with self.assertRaises(ValidationError):
            approved_ruleset_for(self.company.pk, "monthly_payroll", date(2026, 2, 1))
        with self.assertRaises(ValidationError):
            preview_ruleset(self.book, {"salary": 10}, require_approved=True)

    def test_unsafe_expression_is_blocked(self):
        with self.assertRaises(ValidationError):
            VNPayRule.objects.create(
                rule_set=self.book, code="hack", position=40,
                category="net", label="Unsafe", expression="salary.__class__",
            )

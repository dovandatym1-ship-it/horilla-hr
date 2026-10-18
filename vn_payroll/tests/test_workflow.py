"""Database-backed regression tests for approval, isolation and immutability."""

from datetime import date

from django.core.exceptions import PermissionDenied, ValidationError
from django.test import TestCase

from horilla.testkit import make_company, make_user
from vn_payroll.models import FormulaRule
from vn_payroll.services import (
    approve_rule, create_next_version, preview_rule, retire_rule, submit_for_review,
)


class FormulaWorkflowTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.a = make_company("VN Company A")
        cls.b = make_company("VN Company B")
        cls.creator = make_user("vn_formula_creator", is_superuser=True)
        cls.approver = make_user("vn_formula_approver", is_superuser=True)
        cls.intruder = make_user("vn_formula_intruder")

    def rule(self, *, company=None, code="OT_RATE", date_from=None):
        return FormulaRule.objects.create(
            company=company or self.a, code=code, version=1,
            title="Công thức thử nghiệm", category="overtime",
            expression="base_hour * hours * 1.5",
            variables=["base_hour", "hours"], decimal_places=0,
            effective_from=date_from or date(2026, 1, 1),
            created_by=self.creator,
        )

    def approve(self, rule):
        submit_for_review(rule.pk, rule.company_id, self.creator)
        return approve_rule(rule.pk, rule.company_id, self.approver)

    def test_approved_formula_can_be_previewed(self):
        rule = self.approve(self.rule())
        result = preview_rule(
            rule.pk, self.a.pk, self.approver, {"base_hour": "20000", "hours": "3.5"}
        )
        self.assertEqual(str(result["result"]), "105000")
        self.assertEqual(result["version"], 1)

    def test_cross_company_and_missing_role_are_rejected(self):
        rule = self.rule()
        with self.assertRaises(FormulaRule.DoesNotExist):
            preview_rule(rule.pk, self.b.pk, self.approver, {"base_hour": "1", "hours": "1"})
        with self.assertRaises(PermissionDenied):
            preview_rule(rule.pk, self.a.pk, self.intruder, {"base_hour": "1", "hours": "1"})

    def test_creator_cannot_approve_own_rule(self):
        rule = self.rule()
        submit_for_review(rule.pk, self.a.pk, self.creator)
        with self.assertRaises(PermissionDenied):
            approve_rule(rule.pk, self.a.pk, self.creator)

    def test_direct_approval_is_rejected(self):
        rule = self.rule()
        rule.status = "approved"
        rule.approved_by = self.approver
        from django.utils import timezone
        rule.approved_at = timezone.now()
        with self.assertRaises(PermissionDenied):
            rule.save()

    def test_approved_rule_is_immutable(self):
        rule = self.approve(self.rule())
        rule.expression = "base_hour * hours * 2"
        with self.assertRaises(ValidationError):
            rule.save()
        with self.assertRaises(PermissionDenied):
            FormulaRule.objects.filter(pk=rule.pk).update(expression="0")
        with self.assertRaises(PermissionDenied):
            FormulaRule.objects.filter(pk=rule.pk).delete()

    def test_overlapping_approved_rules_are_blocked(self):
        first = self.approve(self.rule())
        second = FormulaRule.objects.create(
            company=self.a, code=first.code, version=2,
            title="Định nghĩa khác", category=first.category,
            expression="base_hour * hours * 2",
            variables=["base_hour", "hours"], effective_from=date(2026, 6, 1),
            created_by=self.creator,
        )
        submit_for_review(second.pk, self.a.pk, self.creator)
        with self.assertRaises(ValidationError):
            approve_rule(second.pk, self.a.pk, self.approver)

    def test_retire_and_create_version(self):
        rule = self.approve(self.rule())
        retire_rule(rule.pk, self.a.pk, self.approver)
        new_rule = create_next_version(rule.pk, self.a.pk, self.creator, date(2027, 1, 1))
        self.assertEqual(new_rule.version, 2)
        self.assertEqual(new_rule.status, "draft")
        self.assertEqual(new_rule.created_by, self.creator)

    def test_invalid_json_variable_is_validation_error(self):
        rule = FormulaRule(
            company=self.a, code="BAD", title="Bad",
            category="tax", expression="gross", variables=[{"unexpected": True}],
            effective_from=date(2026, 1, 1),
        )
        with self.assertRaises(ValidationError):
            rule.full_clean()

    def test_no_false_rejection_of_potential_division_by_zero(self):
        rule = FormulaRule(
            company=self.a, code="RATE", title="Rate", category="earning",
            expression="gross / (days - 1)", variables=["gross", "days"],
            effective_from=date(2026, 1, 1),
        )
        rule.full_clean()  # Syntax valid; actual data may still fail at preview.

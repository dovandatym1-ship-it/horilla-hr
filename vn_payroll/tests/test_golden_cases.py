"""Statutory numbers here are NOT provided; golden cases are illustrative."""

from datetime import date

from django.core.exceptions import ValidationError
from django.test import TestCase

from horilla.testkit import make_company, make_user
from vn_payroll.golden_cases import verify_policy_cases
from vn_payroll.models import FormulaRule
from vn_payroll.services import approve_rule, submit_for_review


class GoldenPolicyTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.company = make_company("VN Golden Policy")
        cls.creator = make_user("vn_golden_creator", is_superuser=True)
        cls.reviewer = make_user("vn_golden_reviewer", is_superuser=True)

    def approve(self, category="insurance", legal_reference="Mẫu giả lập được duyệt"):
        rule = FormulaRule.objects.create(
            company=self.company, code="RATE_TEST", title="Kiểm tra tỷ lệ",
            category=category, expression="base * rate / 100",
            variables=["base", "rate"],
            effective_from=date(2026, 1, 1), created_by=self.creator,
            legal_reference=legal_reference,
        )
        submit_for_review(rule.pk, self.company.pk, self.creator)
        approve_rule(rule.pk, self.company.pk, self.reviewer)
        return rule

    def cases(self):
        return [
            {"inputs": {"base": "0", "rate": "8"}, "expected": "0"},
            {"inputs": {"base": "100", "rate": "8"}, "expected": "8"},
            {"inputs": {"base": "200", "rate": "8"}, "expected": "16"},
        ]

    def test_three_independent_cases_pass(self):
        self.approve()
        report = verify_policy_cases(
            actor=self.reviewer, company_id=self.company.pk,
            code="RATE_TEST", effective_on=date(2026, 10, 1),
            cases=self.cases(),
        )
        self.assertTrue(report["passed"])
        self.assertEqual(report["tested"], 3)
        self.assertEqual(len(report["cases_sha256"]), 64)

    def test_wrong_expected_amount_is_visible(self):
        self.approve()
        cases = self.cases()
        cases[1]["expected"] = "9"
        report = verify_policy_cases(
            actor=self.reviewer, company_id=self.company.pk,
            code="RATE_TEST", effective_on=date(2026, 10, 1),
            cases=cases,
        )
        self.assertFalse(report["passed"])
        self.assertEqual(report["failed_case_numbers"], [2])

    def test_missing_legal_reference_fails(self):
        self.approve(legal_reference="")
        with self.assertRaises(ValidationError):
            verify_policy_cases(
                actor=self.reviewer, company_id=self.company.pk,
                code="RATE_TEST", effective_on=date(2026, 10, 1),
                cases=self.cases(),
            )

    def test_duplicate_case_rejected(self):
        self.approve()
        cases = self.cases()
        cases[2] = cases[1]
        with self.assertRaises(ValidationError):
            verify_policy_cases(
                actor=self.reviewer, company_id=self.company.pk,
                code="RATE_TEST", effective_on=date(2026, 10, 1),
                cases=cases,
            )

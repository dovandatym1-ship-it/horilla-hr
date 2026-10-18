from datetime import date

from django.core.exceptions import ValidationError
from django.test import TestCase

from horilla.testkit import make_company, make_user
from vn_payroll.bridge import preview_from_horilla
from vn_payroll.models import FormulaRule
from vn_payroll.services import approve_rule, submit_for_review


class HorillaPayrollBridgeTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.company = make_company("VN Payroll Bridge Co")
        cls.creator = make_user("vnbridge_creator", is_superuser=True)
        cls.reviewer = make_user("vnbridge_reviewer", is_superuser=True)

    def make_approved_rule(self):
        rule = FormulaRule.objects.create(
            company=self.company,
            code="NET_CHECK",
            version=1,
            title="Dòng đối soát thực lĩnh",
            category="net",
            expression="gross_pay - total_deductions",
            variables=["gross_pay", "total_deductions"],
            effective_from=date(2026, 1, 1),
            created_by=self.creator,
        )
        submit_for_review(rule.pk, self.company.pk, self.creator)
        approve_rule(rule.pk, self.company.pk, self.reviewer)
        return rule

    def test_read_only_preview_uses_horilla_numeric_fields(self):
        self.make_approved_rule()
        payload = {
            "gross_pay": 18000000.0,
            "total_deductions": 1500000.0,
            "employee": object(),
            "net_pay": 16500000.0,
        }
        result = preview_from_horilla(
            company_id=self.company.pk,
            code="NET_CHECK",
            effective_on=date(2026, 10, 1),
            actor=self.reviewer,
            payroll_data=payload,
        )
        self.assertEqual(str(result["result"]), "16500000")
        self.assertEqual(len(result["input_sha256"]), 64)
        self.assertNotIn("employee", result["inputs"])

    def test_nonapproved_rule_fails_closed(self):
        rule = FormulaRule.objects.create(
            company=self.company, code="DRAFT", version=1,
            title="Draft", category="net", expression="gross_pay",
            variables=["gross_pay"], effective_from=date(2026, 1, 1),
            created_by=self.creator,
        )
        with self.assertRaises(ValidationError):
            preview_from_horilla(
                company_id=self.company.pk,
                code=rule.code,
                effective_on=date(2026, 10, 1),
                actor=self.reviewer,
                payroll_data={"gross_pay": 100},
            )

    def test_cannot_override_horilla_source_with_extra_inputs(self):
        self.make_approved_rule()
        with self.assertRaises(ValidationError):
            preview_from_horilla(
                company_id=self.company.pk,
                code="NET_CHECK",
                effective_on=date(2026, 10, 1),
                actor=self.reviewer,
                payroll_data={"gross_pay": 100, "total_deductions": 20},
                extra_inputs={"gross_pay": "999999999"},
            )

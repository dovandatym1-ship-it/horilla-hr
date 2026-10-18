"""Integration tests cover effective dates, approvals, scoping and source facts."""

from datetime import date
from decimal import Decimal

from django.core.exceptions import PermissionDenied, ValidationError
from django.test import TestCase

from horilla.testkit import make_company, make_employee, make_user
from vn_hrm.tests.helpers import existing_or_active_contract
from vn_hrm.models import VNContractAmendment
from vn_hrm.payroll_sources import effective_contract_wage, period_sources
from vn_hrm.services import approve_contract_amendment, submit_contract_amendment


class VietnamPayrollSourceTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.company = make_company("VN sources")
        cls.other_company = make_company("Other VN sources")
        cls.creator = make_user("vn_source_creator", is_superuser=True)
        cls.checker = make_user("vn_source_checker", is_superuser=True)
        cls.employee = make_employee(
            company=cls.company, email="vn-source-employee@example.com"
        )
        cls.contract = existing_or_active_contract(
            cls.employee, start_date=date(2026, 1, 1)
        )

    def make_approved_amendment(self, start=date(2026, 1, 1)):
        amendment = VNContractAmendment.objects.create(
            company=self.company, contract=self.contract,
            version=1, effective_from=start, wage_vnd="20000001",
            created_by=self.creator,
        )
        submit_contract_amendment(
            actor=self.creator, company_id=self.company.pk,
            amendment_id=amendment.pk,
        )
        approve_contract_amendment(
            actor=self.checker, company_id=self.company.pk,
            amendment_id=amendment.pk,
        )
        return amendment

    def test_only_approved_amendment_replaces_legacy_wage_in_preview(self):
        d = date(2026, 4, 30)
        original = effective_contract_wage(
            company_id=self.company.pk, contract=self.contract, on_date=d
        )
        self.assertEqual(original["source"], "legacy_horilla_float")
        self.make_approved_amendment()
        wage = effective_contract_wage(
            company_id=self.company.pk, contract=self.contract, on_date=d
        )
        self.assertEqual(wage["wage"], Decimal("20000001"))
        self.assertEqual(wage["source"], "approved_vn_amendment")

    def test_cross_company_access_is_denied(self):
        with self.assertRaises(PermissionDenied):
            effective_contract_wage(
                company_id=self.other_company.pk,
                contract=self.contract, on_date=date(2026, 4, 30)
            )

    def test_rule_changes_mid_period_fail_closed(self):
        self.make_approved_amendment(start=date(2026, 4, 15))
        with self.assertRaises(ValidationError):
            period_sources(
                actor=self.checker, company_id=self.company.pk,
                employee_id=self.employee.pk, contract_id=self.contract.pk,
                start_date=date(2026, 4, 1), end_date=date(2026, 4, 30),
            )

    def test_empty_approved_leave_and_ot_do_not_create_money(self):
        snapshot = period_sources(
            actor=self.checker, company_id=self.company.pk,
            employee_id=self.employee.pk, contract_id=self.contract.pk,
            start_date=date(2026, 4, 1), end_date=date(2026, 4, 30),
        )
        self.assertEqual(snapshot["inputs"]["vn_approved_ot_hours"], Decimal("0"))
        self.assertEqual(snapshot["inputs"]["vn_approved_leave_days"], Decimal("0"))
        self.assertEqual(len(snapshot["source_sha256"]), 64)

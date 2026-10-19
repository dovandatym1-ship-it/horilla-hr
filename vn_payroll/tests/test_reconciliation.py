"""Immutable reconciliation persistence: no Horilla payout side effects."""
from datetime import date
from decimal import Decimal

from django.core.exceptions import PermissionDenied, ValidationError
from django.test import TestCase

from horilla.testkit import make_company, make_employee, make_user
from vn_hrm.tests.helpers import existing_or_active_contract
from vn_payroll.models import (
    FormulaRule, VNPayrollReconciliationSnapshot,
)
from vn_payroll.reconciliation import record_reconciliation
from vn_payroll.services import approve_rule, submit_for_review


class ReconciliationSnapshotTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.company = make_company("VN Immutable Reconciliation")
        cls.employee = make_employee(
            company=cls.company, email="vn-audit-employee@example.com",
        )
        cls.contract = existing_or_active_contract(
            cls.employee, start_date=date(2026, 1, 1),
        )
        cls.creator = make_user("vn_snapshot_creator", is_superuser=True)
        cls.approver = make_user("vn_snapshot_approver", is_superuser=True)
        cls.intruder = make_user("vn_snapshot_intruder")
        rule = FormulaRule.objects.create(
            company=cls.company, code="VN_WAGE_AUDIT", version=1,
            title="Đối soát tiền lương hợp đồng",
            category="earning", expression="vn_contract_wage",
            variables=["vn_contract_wage"], decimal_places=0,
            effective_from=date(2026, 1, 1), created_by=cls.creator,
        )
        submit_for_review(rule.pk, cls.company.pk, cls.creator)
        approve_rule(rule.pk, cls.company.pk, cls.approver)

    def inputs(self, *, actor=None, payroll_data=None):
        first = date(2026, 4, 1)
        last = date(2026, 4, 30)
        return {
            "actor": actor or self.approver,
            "company_id": self.company.pk,
            "employee_id": self.employee.pk,
            "contract_id": self.contract.pk,
            "start_date": first, "end_date": last,
            "code": "VN_WAGE_AUDIT",
            "payroll_data": payroll_data if payroll_data is not None else {
                "employee": self.employee, "start_date": first, "end_date": last,
            },
        }

    def test_idempotent_append_only_record_never_modifies_payslip(self):
        from payroll.models.models import Payslip

        original_count = Payslip._base_manager.count()
        first = record_reconciliation(**self.inputs())
        second = record_reconciliation(**self.inputs())
        self.assertEqual(first.pk, second.pk)
        self.assertEqual(VNPayrollReconciliationSnapshot._base_manager.count(), 1)
        self.assertEqual(Payslip._base_manager.count(), original_count)
        self.assertEqual(first.rule_version, 1)
        self.assertEqual(len(first.source_sha256), 64)
        self.assertEqual(len(first.record_sha256), 64)
        self.assertEqual(first.result_exact, Decimal("30000"))
        first.result_exact = Decimal("1")
        with self.assertRaises(PermissionDenied):
            first.save()
        with self.assertRaises(PermissionDenied):
            VNPayrollReconciliationSnapshot.objects.filter(
                pk=first.pk
            ).update(result_exact=Decimal("1"))

    def test_permission_and_payload_mismatch_are_denied(self):
        with self.assertRaises(PermissionDenied):
            record_reconciliation(**self.inputs(actor=self.intruder))
        with self.assertRaises(ValidationError):
            record_reconciliation(**self.inputs(payroll_data={
                "employee": self.employee, "start_date": date(2026, 3, 1),
                "end_date": date(2026, 4, 30),
            }))
        self.assertEqual(VNPayrollReconciliationSnapshot._base_manager.count(), 0)

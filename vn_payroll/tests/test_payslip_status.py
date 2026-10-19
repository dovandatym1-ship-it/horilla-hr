"""Integration tests for payslip status workflow security and atomicity."""
from datetime import date

from django.core.exceptions import PermissionDenied, ValidationError
from django.test import TestCase

from horilla.testkit import make_company, make_employee, make_user
from payroll.models.models import Payslip
from vn_payroll.payslip_status import (
    change_many_payslip_statuses, change_payslip_status,
)


class PayslipStatusGateTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.company = make_company("VN status controls")
        cls.admin = make_user("vn_status_admin", is_superuser=True)
        cls.other = make_user("vn_status_no_access")
        cls.employee = make_employee(
            company=cls.company, email="vn-status-employee@example.com"
        )

    def create_slip(self, period_start=date(2026, 10, 1), status="draft"):
        return Payslip._base_manager.create(
            employee_id=self.employee, start_date=period_start,
            end_date=date(2026, 10, 31), pay_head_data={},
            status=status, gross_pay=1000, net_pay=900, deduction=100,
        )

    def test_valid_and_invalid_transitions(self):
        slip = self.create_slip()
        change_payslip_status(actor=self.admin, payslip_id=slip.pk, target_status="confirmed")
        slip.refresh_from_db()
        self.assertEqual(slip.status, "confirmed")
        with self.assertRaises(ValidationError):
            change_payslip_status(actor=self.admin, payslip_id=slip.pk, target_status="draft")
        change_payslip_status(actor=self.admin, payslip_id=slip.pk, target_status="paid")
        with self.assertRaises(ValidationError):
            change_payslip_status(actor=self.admin, payslip_id=slip.pk, target_status="draft")

    def test_unpermitted_actor_fails_closed(self):
        slip = self.create_slip()
        with self.assertRaises(PermissionDenied):
            change_payslip_status(actor=self.other, payslip_id=slip.pk, target_status="confirmed")

    def test_bulk_atomic_validation(self):
        one = self.create_slip(status="confirmed")
        two = self.create_slip(period_start=date(2026, 9, 1))
        with self.assertRaises(ValidationError):
            change_many_payslip_statuses(
                actor=self.admin, payslip_ids=[one.pk, two.pk], target_status="paid"
            )
        one.refresh_from_db()
        two.refresh_from_db()
        self.assertEqual(one.status, "confirmed")
        self.assertEqual(two.status, "draft")

    def test_invalid_id_and_status_denied(self):
        slip = self.create_slip()
        with self.assertRaises(ValidationError):
            change_many_payslip_statuses(actor=self.admin, payslip_ids=[slip.pk, slip.pk], target_status="confirmed")
        with self.assertRaises(ValidationError):
            change_payslip_status(actor=self.admin, payslip_id=slip.pk, target_status="unvalidated")

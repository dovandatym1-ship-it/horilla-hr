"""Company-scoped Vietnam management payroll report tests (not statutory)."""
from datetime import date
from decimal import Decimal
from io import StringIO
import csv

from django.core.exceptions import PermissionDenied, ValidationError
from django.test import TestCase

from horilla.testkit import make_company, make_employee, make_user
from payroll.models.models import Payslip
from vn_hrm.reports import payroll_period_summary, payroll_period_summary_csv


class VietnamPayrollReportsTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.a = make_company("VN Reporting Company")
        cls.b = make_company("Other Reporting Company")
        cls.admin = make_user("vn_report_admin", is_superuser=True)
        cls.no_access = make_user("vn_report_no_access")
        cls.employee_a = make_employee(
            company=cls.a, email="vn-report-a@example.com"
        )
        cls.employee_b = make_employee(
            company=cls.b, email="vn-report-b@example.com"
        )

    def slip(self, employee, status, *, start=date(2026, 4, 1), end=date(2026, 4, 30)):
        return Payslip._base_manager.create(
            employee_id=employee, start_date=start, end_date=end,
            pay_head_data={}, status=status,
            gross_pay=1000000, deduction=100000, net_pay=900000,
        )

    def report(self, *, actor=None):
        return payroll_period_summary(
            actor=actor or self.admin, company_id=self.a.pk,
            start_date=date(2026, 4, 1), end_date=date(2026, 4, 30),
        )

    def test_paid_and_confirmed_only_no_cross_tenant_data(self):
        self.slip(self.employee_a, "confirmed")
        self.slip(self.employee_a, "draft", start=date(2026, 4, 2))
        self.slip(self.employee_b, "paid")
        result = self.report()
        self.assertEqual(result["payslip_count"], 1)
        self.assertEqual(result["confirmed_count"], 1)
        self.assertEqual(result["paid_count"], 0)
        self.assertEqual(result["gross_total_vnd"], Decimal("1000000"))
        self.assertEqual(result["deduction_total_vnd"], Decimal("100000"))
        self.assertEqual(result["net_total_vnd"], Decimal("900000"))
        self.assertFalse(result["is_statutory_report"])

    def test_reject_unpermitted_actor(self):
        with self.assertRaises(PermissionDenied):
            self.report(actor=self.no_access)

    def test_prevent_double_count_same_employee_period(self):
        self.slip(self.employee_a, "confirmed")
        self.slip(self.employee_a, "paid")
        with self.assertRaises(ValidationError):
            self.report()

    def test_csv_contains_only_aggregates(self):
        self.slip(self.employee_a, "paid")
        payload = payroll_period_summary_csv(
            actor=self.admin, company_id=self.a.pk,
            start_date=date(2026, 4, 1), end_date=date(2026, 4, 30),
        )
        rows = list(csv.DictReader(StringIO(payload)))
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["paid_count"], "1")
        self.assertEqual(rows[0]["deduction_total_vnd"], "100000")
        self.assertNotIn(self.employee_a.email, payload)
        self.assertNotIn("employee_id", rows[0])

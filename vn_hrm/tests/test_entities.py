"""Regression tests for additional Vietnam HRM models.

No statutory calculations or mutations of Horilla Attendance/AvailableLeave
are asserted; those integrations require business/legal signoff.
"""

from datetime import date
from decimal import Decimal

from django.core.exceptions import ValidationError
from django.test import TestCase
from django.utils import timezone

from horilla.testkit import make_company, make_employee, make_leave_type, make_user
from vn_hrm.models import (
    VNAttendanceCorrection,
    VNDependent,
    VNEmployeeLegalProfile,
    VNLeaveLedgerEntry,
)


class VNHRMDataTests(TestCase):
    def setUp(self):
        self.company = make_company(name="Vietnam Company")
        self.other_company = make_company(name="Other Company", address="Other St")
        self.employee = make_employee(
            company=self.company, email="vn-employees-test@hrm.example"
        )

    def test_identity_keeps_only_masked_suffix_and_opaque_vault_ref(self):
        profile = VNEmployeeLegalProfile.objects.create(
            employee=self.employee, company=self.company,
            citizen_id_suffix="1234", citizen_id_vault_ref="vault-key-1",
        )
        self.assertEqual(profile.citizen_id_suffix, "1234")
        self.assertEqual(profile.residency_type, "unverified")
        profile.citizen_id_suffix = "123456789012"
        with self.assertRaises(ValidationError):
            profile.save()

    def test_employee_company_must_match(self):
        with self.assertRaises(ValidationError):
            VNEmployeeLegalProfile.objects.create(
                employee=self.employee, company=self.other_company
            )

    def test_dependent_is_effective_dated_and_not_auto_eligible(self):
        item = VNDependent.objects.create(
            employee=self.employee, company=self.company,
            full_name="Người phụ thuộc thử nghiệm", relationship="child",
            eligible_from=date(2026, 1, 1),
        )
        self.assertEqual(item.verification_status, "pending")
        item.eligible_to = date(2025, 12, 31)
        with self.assertRaises(ValidationError):
            item.save()

    def test_attendance_correction_stores_decision_without_modifying_source(self):
        item = VNAttendanceCorrection.objects.create(
            company=self.company, employee=self.employee,
            work_date=date(2026, 10, 18), requested_minutes=30,
            reason="Thiếu bản ghi ra ca",
        )
        self.assertEqual(item.status, "pending")
        item.status = "approved"
        item.reviewed_by = make_user("reviewer_vn_attendance")
        item.reviewed_at = timezone.now()
        item.save()
        item.reason = "Tự sửa sau phê duyệt"
        with self.assertRaises(ValidationError):
            item.save()

    def test_leave_ledger_is_idempotent_and_append_only(self):
        leave_type = make_leave_type(name="Annual VN Test")
        entry = VNLeaveLedgerEntry.objects.create(
            company=self.company, employee=self.employee,
            leave_type=leave_type, source_key="approval:vn-001",
            effective_date=date(2026, 10, 18),
            units=Decimal("-0.50"), reason="Nghỉ nửa ngày",
        )
        self.assertEqual(entry.units, Decimal("-0.50"))
        with self.assertRaises(ValidationError):
            entry.delete()
        entry.reason = "Sửa trái phép"
        with self.assertRaises(ValidationError):
            entry.save()
        with self.assertRaises(ValidationError):
            VNLeaveLedgerEntry.objects.create(
                company=self.company, employee=self.employee,
                leave_type=leave_type, source_key="approval:vn-001",
                effective_date=date(2026, 10, 18), units=Decimal("-0.50"),
                reason="Gửi lại cùng sự kiện",
            )

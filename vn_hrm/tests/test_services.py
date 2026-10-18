from datetime import date
from decimal import Decimal

from cryptography.fernet import Fernet
from django.core.exceptions import PermissionDenied, ValidationError
from django.test import TestCase, override_settings

from horilla.testkit import make_company, make_employee, make_user
from vn_hrm.models import VNSensitiveAccessAudit
from vn_hrm.services import (
    add_dependent, leave_balance, read_identifier, record_leave_event,
    save_identifier, verify_dependent,
)


class VietnameseHrmServicesTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.company = make_company("VNHRM Company")
        cls.other_company = make_company("VNHRM Other Company")
        cls.admin = make_user("vnhrm_admin", is_superuser=True)
        cls.other_user = make_user("vnhrm_plain_user")
        cls.emp = make_employee(
            company=cls.company, email="vnhrm-employee@example.com", user=cls.other_user
        )

    def test_identifier_is_encrypted_and_access_audited(self):
        key = Fernet.generate_key().decode("ascii")
        with override_settings(VN_PII_FERNET_KEY=key):
            profile = save_identifier(
                actor=self.admin, company_id=self.company.pk,
                employee_id=self.emp.pk, kind="citizen",
                value="012345678901",
            )
            profile.refresh_from_db()
            self.assertNotIn("012345678901", profile.citizen_ciphertext)
            self.assertEqual(
                read_identifier(
                    actor=self.admin, company_id=self.company.pk,
                    employee_id=self.emp.pk, kind="citizen",
                    purpose="Đối soát hồ sơ nhân viên", masked=True,
                ),
                "********8901",
            )
            self.assertEqual(VNSensitiveAccessAudit.objects.count(), 2)

    def test_cross_company_write_is_denied(self):
        key = Fernet.generate_key().decode("ascii")
        with override_settings(VN_PII_FERNET_KEY=key):
            with self.assertRaises(PermissionDenied):
                save_identifier(
                    actor=self.admin, company_id=self.other_company.pk,
                    employee_id=self.emp.pk, kind="citizen",
                    value="012345678901",
                )

    def test_user_without_permission_cannot_reveal(self):
        with self.assertRaises(PermissionDenied):
            read_identifier(
                actor=self.other_user, company_id=self.company.pk,
                employee_id=self.emp.pk, kind="citizen",
                purpose="Đối soát hồ sơ nhân viên", masked=False,
            )

    def test_dependent_requires_valid_period(self):
        with self.assertRaises(ValidationError):
            add_dependent(
                actor=self.admin, company_id=self.company.pk,
                employee_id=self.emp.pk, name="Con A", relation="child",
                valid_from=date(2026, 10, 18), valid_to=date(2025, 1, 1),
            )
        dep = add_dependent(
            actor=self.admin, company_id=self.company.pk,
            employee_id=self.emp.pk, name="Con A", relation="child",
            valid_from=date(2026, 10, 18),
        )
        verify_dependent(actor=self.admin, company_id=self.company.pk, dependent_id=dep.pk)
        dep.refresh_from_db()
        self.assertEqual(dep.status, "verified")

    def test_leave_ledger_is_idempotent_and_signed(self):
        params = dict(
            actor=self.admin, company_id=self.company.pk,
            employee_id=self.emp.pk, source_event_key="leave-req-1",
            event_type="debit", units="-1.000", effective_on=date(2026, 10, 18),
        )
        first = record_leave_event(**params)
        second = record_leave_event(**params)
        self.assertEqual(first.pk, second.pk)
        self.assertEqual(
            leave_balance(
                actor=self.admin, company_id=self.company.pk,
                employee_id=self.emp.pk,
            ),
            Decimal("-1.000"),
        )
        with self.assertRaises(ValidationError):
            record_leave_event(**{**params, "units": "-2.000"})
        with self.assertRaises(ValidationError):
            record_leave_event(
                **{**params, "source_event_key": "bad", "units": "1.0"}
            )

    def test_ledger_event_cannot_be_changed_or_deleted(self):
        event = record_leave_event(
            actor=self.admin, company_id=self.company.pk,
            employee_id=self.emp.pk, source_event_key="credit-1",
            event_type="credit", units="2.000", effective_on=date(2026, 10, 18),
        )
        event.units = Decimal("10")
        with self.assertRaises(PermissionDenied):
            event.save()
        with self.assertRaises(PermissionDenied):
            event.delete()

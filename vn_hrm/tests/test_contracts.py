"""Contract amendments are independent snapshots, not applied to payroll yet."""

from datetime import date

from django.core.exceptions import PermissionDenied, ValidationError
from django.test import TestCase

from horilla.testkit import make_company, make_employee, make_user
from vn_hrm.tests.helpers import existing_or_active_contract
from vn_hrm.models import VNContractAmendment
from vn_hrm.services import approve_contract_amendment, submit_contract_amendment


class ContractAmendmentTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.company = make_company("VN Contracts")
        cls.creator = make_user("vn_contract_creator", is_superuser=True)
        cls.reviewer = make_user("vn_contract_reviewer", is_superuser=True)
        cls.employee = make_employee(
            company=cls.company, email="vncontract-employee@example.com"
        )
        cls.contract = existing_or_active_contract(
            cls.employee, start_date=date(2026, 1, 1)
        )

    def amendment(self, version=1, *, effective_from=None):
        return VNContractAmendment.objects.create(
            company=self.company,
            contract=self.contract,
            version=version,
            effective_from=effective_from or date(2026, 1, 1),
            wage_vnd="20000000",
            created_by=self.creator,
        )

    def test_maker_checker_and_immutability(self):
        obj = self.amendment()
        submit_contract_amendment(
            actor=self.creator, company_id=self.company.pk, amendment_id=obj.pk
        )
        with self.assertRaises(PermissionDenied):
            approve_contract_amendment(
                actor=self.creator, company_id=self.company.pk, amendment_id=obj.pk
            )
        approve_contract_amendment(
            actor=self.reviewer, company_id=self.company.pk, amendment_id=obj.pk
        )
        obj.refresh_from_db()
        self.assertEqual(obj.status, "approved")
        obj.wage_vnd = "21000000"
        with self.assertRaises(PermissionDenied):
            obj.save()
        with self.assertRaises(PermissionDenied):
            VNContractAmendment.objects.filter(pk=obj.pk).update(wage_vnd=1)

    def test_overlap_prevention(self):
        obj = self.amendment()
        submit_contract_amendment(
            actor=self.creator, company_id=self.company.pk, amendment_id=obj.pk
        )
        approve_contract_amendment(
            actor=self.reviewer, company_id=self.company.pk, amendment_id=obj.pk
        )
        other = self.amendment(2, effective_from=date(2026, 5, 1))
        submit_contract_amendment(
            actor=self.creator, company_id=self.company.pk, amendment_id=other.pk
        )
        with self.assertRaises(ValidationError):
            approve_contract_amendment(
                actor=self.reviewer, company_id=self.company.pk,
                amendment_id=other.pk,
            )

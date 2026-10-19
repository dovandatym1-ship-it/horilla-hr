"""Test-only contract fixture: Employee signal can pre-create an active contract."""

from datetime import date

from payroll.models.models import Contract
from payroll.tests.factories_payroll import make_active_contract


def existing_or_active_contract(employee, *, start_date=date(2026, 1, 1)):
    """Reuse existing signal-created contract instead of introducing an overlap.

    Horilla employee provisioning sometimes creates an active contract. The
    contract uniqueness invariant must remain enforced in production.
    """
    existing = Contract._base_manager.filter(
        employee_id=employee, contract_status="active"
    ).first()
    if existing is None:
        return make_active_contract(
            employee, contract_start_date=start_date
        )
    Contract._base_manager.filter(pk=existing.pk).update(
        contract_start_date=start_date, contract_end_date=None,
        wage=30000.0,
    )
    existing.refresh_from_db()
    return existing

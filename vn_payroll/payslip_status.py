"""Tenant-scoped, atomic state changes for Horilla payslips.

No bulk UPDATE bypass, arbitrary status injection or Paid -> Draft reset.
This controls review metadata only; it is NOT banking disbursement.
"""
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction

from payroll.models.models import Payslip
from .services import require_permission

TRANSITIONS = {
    "draft": frozenset({"review_ongoing", "confirmed"}),
    "review_ongoing": frozenset({"draft", "confirmed"}),
    "confirmed": frozenset({"paid"}),
    "paid": frozenset(),
}


def _validate_target(target_status):
    if not isinstance(target_status, str) or target_status not in TRANSITIONS:
        raise ValidationError("Trạng thái phiếu lương không hợp lệ.")


@transaction.atomic
def change_many_payslip_statuses(*, actor, payslip_ids, target_status):
    """All-or-nothing update, with record ownership/permission per company."""
    _validate_target(target_status)
    if (
        not isinstance(payslip_ids, list)
        or not payslip_ids
        or len(payslip_ids) > 500
        or any(not isinstance(i, int) or isinstance(i, bool) or i <= 0 for i in payslip_ids)
        or len(set(payslip_ids)) != len(payslip_ids)
    ):
        raise ValidationError("Danh sách phiếu lương không hợp lệ/không được trùng.")
    rows = list(
        Payslip._base_manager.select_related(
            "employee_id__employee_work_info"
        ).select_for_update(of=("self",)).filter(pk__in=payslip_ids).order_by("pk")
    )
    if len(rows) != len(payslip_ids):
        raise ValidationError("Có phiếu lương không tồn tại; không cập nhật một phần.")
    for slip in rows:
        work_info = getattr(slip.employee_id, "employee_work_info", None)
        company_id = getattr(work_info, "company_id_id", None)
        if not isinstance(company_id, int):
            raise PermissionDenied("Phiếu lương thiếu pháp nhân hợp lệ.")
        require_permission(actor, company_id, "change_payslip")
        current = slip.status
        if current not in TRANSITIONS:
            raise ValidationError("Trạng thái nguồn phiếu lương không hợp lệ.")
        if current != target_status and target_status not in TRANSITIONS[current]:
            raise ValidationError("Không được chuyển trạng thái phiếu lương theo cách này.")
    for slip in rows:
        if slip.status != target_status:
            slip.status = target_status
            slip.save(update_fields=["status"])
    return len(rows)


def change_payslip_status(*, actor, payslip_id, target_status):
    """Singleton form of the exact same approval workflow."""
    change_many_payslip_statuses(
        actor=actor, payslip_ids=[int(payslip_id)],
        target_status=target_status,
    )
    return Payslip._base_manager.get(pk=payslip_id)

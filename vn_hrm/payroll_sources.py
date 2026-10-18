"""Authorized, read-only sourcing of Vietnamese contract, leave and overtime data.

No hook into payslip writes or payment processing. Fail closed if a period spans
an amendment boundary, leave request is partially outside the period, or
an approved amount would be ambiguous. This is a reconciliation/preview layer.
"""

from datetime import date
from decimal import Decimal
from hashlib import sha256
import json

from django.core.exceptions import PermissionDenied, ValidationError
from django.db.models import Q

from attendance.models import Attendance
from leave.models import LeaveRequest
from payroll.models.models import Contract
from vn_payroll.bridge import preview_from_horilla
from vn_payroll.decimal_tools import as_decimal
from vn_payroll.services import require_permission

from .models import VNContractAmendment, VNLeaveLedgerEvent
from .services import require_company_permission, require_current_employee_in_company


def _period(start_date, end_date):
    if not isinstance(start_date, date) or not isinstance(end_date, date):
        raise ValidationError("Kỳ lương phải là ngày hợp lệ.")
    if end_date < start_date or (end_date - start_date).days > 366:
        raise ValidationError("Kỳ lương không hợp lệ (tối đa 367 ngày).")


def effective_contract_wage(*, company_id, contract, on_date):
    """Read a single approved salary amendment effective on the requested day.

    Wages of hourly/daily/CTC contracts MUST NOT be used as monthly base; the
    caller receives wage_type and source and must apply its own approved policy.
    """
    if not isinstance(on_date, date):
        raise ValidationError("Ngày áp dụng hợp đồng không hợp lệ.")
    if contract.employee_id.employee_work_info.company_id_id != company_id:
        raise PermissionDenied("Hợp đồng thuộc pháp nhân khác.")
    if contract.contract_status != "active":
        raise ValidationError("Hợp đồng chưa ở trạng thái có hiệu lực.")
    if contract.contract_start_date > on_date or (
        contract.contract_end_date and contract.contract_end_date < on_date
    ):
        raise ValidationError("Hợp đồng nằm ngoài ngày hiệu lực.")
    candidates = list(
        VNContractAmendment._base_manager.filter(
            company_id=company_id, contract_id=contract.pk, status="approved",
            effective_from__lte=on_date,
        ).filter(Q(effective_to__isnull=True) | Q(effective_to__gte=on_date))[:2]
    )
    if len(candidates) > 1:
        raise ValidationError("Nhiều phụ lục cùng có hiệu lực; dừng đối soát.")
    if candidates:
        item = candidates[0]
        return {
            "wage": as_decimal(item.wage_vnd, field="Lương phụ lục"),
            "source": "approved_vn_amendment",
            "source_id": item.pk,
            "version": item.version,
            "wage_type": contract.wage_type,
        }
    if contract.pay_rate is None:
        raise ValidationError("Hợp đồng chưa có mức lương hoặc đơn giá giờ.")
    return {
        "wage": as_decimal(contract.pay_rate, field="Mức lương/đơn giá Horilla"),
        "source": "legacy_horilla_float",
        "source_id": contract.pk,
        "version": None,
        "wage_type": contract.wage_type,
    }


def _check_amendment_boundaries(*, company_id, contract_id, start_date, end_date):
    """Reject any salary change inside a payroll period (must split periods)."""
    changes = VNContractAmendment._base_manager.filter(
        company_id=company_id, contract_id=contract_id, status="approved"
    ).filter(
        Q(effective_from__gt=start_date, effective_from__lte=end_date)
        | Q(effective_to__gte=start_date, effective_to__lt=end_date)
    )
    if changes.exists():
        raise ValidationError(
            "Phụ lục đổi mức lương giữa kỳ; cần tách kỳ trước khi tính."
        )


def period_sources(
    *, actor, company_id, employee_id, contract_id, start_date, end_date
):
    """A canonical, Decimal-only, authorized snapshot of approved source facts.

    Leave balance is informational and MUST NOT be subtracted from payroll
    again; Horilla's existing engine may already deduct approved leave.
    """
    require_permission(actor, company_id, "preview_formularule")
    require_company_permission(actor, company_id, "view_vnleaveledgerevent")
    _period(start_date, end_date)
    require_current_employee_in_company(employee_id, company_id)
    try:
        contract = Contract._base_manager.select_related(
            "employee_id__employee_work_info"
        ).get(pk=contract_id, employee_id=employee_id)
    except Contract.DoesNotExist as exc:
        raise ValidationError("Không tìm thấy hợp đồng nhân viên tương ứng.") from exc
    if start_date < contract.contract_start_date or (
        contract.contract_end_date and end_date > contract.contract_end_date
    ):
        raise ValidationError("Kỳ lương nằm ngoài hiệu lực hợp đồng.")
    _check_amendment_boundaries(
        company_id=company_id, contract_id=contract_id,
        start_date=start_date, end_date=end_date,
    )
    wage = effective_contract_wage(
        company_id=company_id, contract=contract, on_date=end_date
    )

    approved_leave = LeaveRequest._base_manager.filter(
        employee_id=employee_id, status="approved",
        start_date__lte=end_date,
    ).filter(
        Q(end_date__gte=start_date)
        | Q(end_date__isnull=True, start_date__gte=start_date)
    ).select_related("leave_type_id")
    leave_days = Decimal("0")
    unpaid_leave = Decimal("0")
    leave_ids = []
    for request in approved_leave:
        # Requested days is for the WHOLE request. Prorating across pay
        # periods using days-in-range would silently misprice half-day,
        # schedule and holiday rules. Require an explicit split upstream.
        leave_end = request.end_date or request.start_date
        if request.start_date < start_date or leave_end > end_date:
            raise ValidationError("Nghỉ phép giao hai kỳ; cần phân bổ theo ngày.")
        days = as_decimal(request.requested_days, field="Số ngày nghỉ đã duyệt")
        if days < 0:
            raise ValidationError("Số ngày nghỉ không hợp lệ.")
        leave_days += days
        if request.leave_type_id.payment == "unpaid":
            unpaid_leave += days
        leave_ids.append(request.pk)

    attendance = Attendance._base_manager.filter(
        employee_id=employee_id, attendance_date__gte=start_date,
        attendance_date__lte=end_date,
        attendance_validated=True, attendance_overtime_approve=True,
    ).only("pk", "approved_overtime_second")
    ot_seconds = 0
    attendance_ids = []
    for entry in attendance:
        secs = entry.approved_overtime_second
        if not isinstance(secs, int) or isinstance(secs, bool) or secs < 0:
            raise ValidationError("Số giây OT được duyệt không hợp lệ.")
        ot_seconds += secs
        attendance_ids.append(entry.pk)
    ot_hours = Decimal(ot_seconds) / Decimal("3600")

    events = VNLeaveLedgerEvent._base_manager.filter(
        company_id=company_id, employee_id=employee_id,
        effective_on__lte=end_date,
    ).only("units")
    balance = sum((event.units for event in events), Decimal("0"))

    inputs = {
        "vn_contract_wage": wage["wage"],
        "vn_approved_leave_days": leave_days,
        "vn_unpaid_leave_days": unpaid_leave,
        "vn_approved_ot_hours": ot_hours,
        "vn_leave_balance": balance,
    }
    evidence = {
        "company_id": company_id, "employee_id": employee_id,
        "contract_id": contract_id,
        "start_date": start_date.isoformat(), "end_date": end_date.isoformat(),
        "wage_source": wage["source"], "wage_source_id": wage["source_id"],
        "wage_version": wage["version"],
        "wage_type": wage["wage_type"],
        "leave_request_ids": sorted(leave_ids),
        "approved_attendance_ids": sorted(attendance_ids),
        "inputs": {key: str(val) for key, val in inputs.items()},
    }
    digest = sha256(json.dumps(
        evidence, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")).hexdigest()
    return {"inputs": inputs, "source_sha256": digest, "evidence": evidence}


def preview_with_hrm_sources(
    *, actor, company_id, employee_id, contract_id, start_date, end_date,
    code, payroll_data
):
    """Reconcile a configured rule with approved HRM source facts, no writes.

    FormulaRule.variables may name vn_* variables explicitly; they cannot
    override reserved Horilla engine variables or quietly affect net pay.
    """
    if not isinstance(payroll_data, dict):
        raise ValidationError("Không có payload tính lương nguồn hợp lệ.")
    payload_employee = payroll_data.get("employee")
    if (
        getattr(payload_employee, "pk", None) != employee_id
        or payroll_data.get("start_date") != start_date
        or payroll_data.get("end_date") != end_date
    ):
        raise ValidationError(
            "Payload tính lương không khớp nhân viên/kỳ nguồn đã phê duyệt."
        )
    snapshot = period_sources(
        actor=actor, company_id=company_id, employee_id=employee_id,
        contract_id=contract_id, start_date=start_date, end_date=end_date,
    )
    # All VN inputs are controlled here, not provided by the calling client.
    from vn_payroll.bridge import rule_for_date, HORILLA_NUMERIC_INPUTS

    rule = rule_for_date(company_id=company_id, code=code, effective_on=end_date)
    extras = {
        key: str(value) for key, value in snapshot["inputs"].items()
        if key in rule.variables
    }
    if set(extras) & HORILLA_NUMERIC_INPUTS:
        raise ValidationError("Không thể ghi đè biến lương Horilla.")
    result = preview_from_horilla(
        actor=actor, company_id=company_id, code=code,
        effective_on=end_date, payroll_data=payroll_data, extra_inputs=extras,
    )
    result["hrm_source_sha256"] = snapshot["source_sha256"]
    result["hrm_source"] = {
        key: value for key, value in snapshot["evidence"].items()
        if key not in ("company_id", "employee_id", "inputs")
    }
    result["mode"] = "READ_ONLY_RECONCILIATION_NOT_FOR_PAYMENT"
    return result

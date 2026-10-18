"""Explicit company-scoped services for Vietnamese HRM private data."""

from decimal import Decimal

from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction
from django.db.models import Sum
from django.utils import timezone

from base.auth_backends import (
    get_allowed_company_ids,
    get_effective_permission_codenames,
)
from base.models import Company
from employee.models import Employee
from .crypto import mask_identifier, reveal_identifier
from .approval_guard import allow_hr_approval
from .models import (
    VNDependent,
    VNContractAmendment,
    VNEmployeeLegalProfile,
    VNLeaveLedgerEvent,
    VNSensitiveAccessAudit,
)


def require_company_permission(actor, company_id, codename):
    if not getattr(actor, "is_authenticated", False) or not actor.is_active:
        raise PermissionDenied("Tài khoản không hợp lệ.")
    if isinstance(company_id, bool) or not isinstance(company_id, int):
        raise PermissionDenied("Pháp nhân không hợp lệ.")
    if actor.is_superuser:
        return
    if company_id not in get_allowed_company_ids(actor):
        raise PermissionDenied("Không có quyền truy cập pháp nhân.")
    if codename not in get_effective_permission_codenames(
        actor, company_id=company_id
    ):
        raise PermissionDenied("Không được thực hiện chức năng này.")


def require_current_employee_in_company(employee_id, company_id):
    try:
        employee = Employee.objects.select_related("employee_work_info").get(
            pk=employee_id
        )
        assigned_company = employee.employee_work_info.company_id_id
    except (Employee.DoesNotExist, AttributeError):
        raise ValidationError("Nhân viên không có hồ sơ công tác hợp lệ.")
    if assigned_company != company_id:
        raise PermissionDenied("Nhân viên không thuộc pháp nhân đang xử lý.")
    return employee


@transaction.atomic
def save_identifier(*, actor, company_id, employee_id, kind, value):
    require_company_permission(actor, company_id, "manage_vn_identifiers")
    employee = require_current_employee_in_company(employee_id, company_id)
    Company.objects.select_for_update().get(pk=company_id)
    profile, _ = VNEmployeeLegalProfile._base_manager.select_for_update().get_or_create(
        company_id=company_id,
        employee=employee,
    )
    profile.set_identifier(kind, value)  # requires a configured Fernet key
    profile.full_clean()  # includes uniqueness validation for citizen HMAC
    profile.save()
    VNSensitiveAccessAudit.objects.create(
        company_id=company_id, employee=employee, actor=actor,
        purpose="Cập nhật thông tin pháp lý theo nghiệp vụ nhân sự",
        action="set_" + kind,
    )
    return profile


@transaction.atomic
def read_identifier(*, actor, company_id, employee_id, kind, purpose, masked=True):
    require_company_permission(actor, company_id, "reveal_vn_identifiers")
    if not isinstance(purpose, str) or len(purpose.strip()) < 5 or len(purpose) > 255:
        raise ValidationError("Cần lý do truy cập cụ thể.")
    fields = {
        "citizen": "citizen_ciphertext",
        "tax": "tax_ciphertext",
        "insurance": "insurance_ciphertext",
    }
    if kind not in fields:
        raise ValidationError("Loại thông tin cần xem không hợp lệ.")
    employee = require_current_employee_in_company(employee_id, company_id)
    profile = VNEmployeeLegalProfile._base_manager.get(
        company_id=company_id, employee=employee,
    )
    value = getattr(profile, fields[kind])
    if not value:
        raise ValidationError("Chưa có thông tin định danh.")
    plain = reveal_identifier(value)
    VNSensitiveAccessAudit.objects.create(
        company_id=company_id, employee=employee, actor=actor,
        purpose=purpose.strip(),
        action="masked_" + kind if masked else "reveal_" + kind,
    )
    return mask_identifier(plain) if masked else plain


@transaction.atomic
def add_dependent(*, actor, company_id, employee_id, name, relation, valid_from, valid_to=None):
    require_company_permission(actor, company_id, "add_vndependent")
    employee = require_current_employee_in_company(employee_id, company_id)
    obj = VNDependent(
        company_id=company_id, employee=employee, name=name,
        relation=relation, valid_from=valid_from, valid_to=valid_to,
    )
    obj.full_clean()
    obj.save()
    return obj


@transaction.atomic
def verify_dependent(*, actor, company_id, dependent_id):
    require_company_permission(actor, company_id, "change_vndependent")
    obj = VNDependent._base_manager.select_for_update().get(
        pk=dependent_id, company_id=company_id
    )
    obj.verified_by = actor
    obj.status = "verified"
    obj.full_clean()
    with allow_hr_approval():
        obj.save()
    return obj


@transaction.atomic
def record_leave_event(
    *, actor, company_id, employee_id, source_event_key, event_type,
    units, effective_on, reason=""
):
    require_company_permission(actor, company_id, "add_vnleaveledgerevent")
    employee = require_current_employee_in_company(employee_id, company_id)
    Company.objects.select_for_update().get(pk=company_id)
    defaults = {
        "employee": employee,
        "units": Decimal(str(units)),
        "effective_on": effective_on,
        "reason": reason,
        "created_by": actor,
    }
    existing = VNLeaveLedgerEvent._base_manager.filter(
        company_id=company_id, source_event_key=source_event_key,
        event_type=event_type,
    ).first()
    if existing:
        if (
            existing.employee_id != employee_id
            or existing.units != defaults["units"]
            or existing.effective_on != effective_on
        ):
            raise ValidationError("Khóa sự kiện đã được dùng với dữ liệu khác.")
        return existing
    event = VNLeaveLedgerEvent(
        company_id=company_id,
        source_event_key=source_event_key,
        event_type=event_type,
        **defaults,
    )
    event.save()
    return event


def leave_balance(*, actor, company_id, employee_id):
    require_company_permission(actor, company_id, "view_vnleaveledgerevent")
    require_current_employee_in_company(employee_id, company_id)
    total = VNLeaveLedgerEvent._base_manager.filter(
        company_id=company_id, employee_id=employee_id
    ).aggregate(total=Sum("units"))["total"]
    return total if total is not None else Decimal("0")


@transaction.atomic
def submit_contract_amendment(*, actor, company_id, amendment_id):
    require_company_permission(actor, company_id, "change_vncontractamendment")
    amendment = VNContractAmendment._base_manager.select_for_update().get(
        pk=amendment_id, company_id=company_id
    )
    if amendment.status != "draft":
        raise ValidationError("Chỉ được gửi duyệt phụ lục ở trạng thái nháp.")
    if amendment.created_by_id is None:
        amendment.created_by = actor
    amendment.status = "review"
    amendment.save()
    return amendment


@transaction.atomic
def approve_contract_amendment(*, actor, company_id, amendment_id):
    require_company_permission(actor, company_id, "approve_vncontractamendment")
    Company.objects.select_for_update().get(pk=company_id)
    amendment = VNContractAmendment._base_manager.select_for_update().get(
        pk=amendment_id, company_id=company_id
    )
    if amendment.status != "review":
        raise ValidationError("Phụ lục chưa gửi duyệt.")
    if amendment.created_by_id is None or amendment.created_by_id == actor.pk:
        raise PermissionDenied("Người lập và người duyệt phụ lục phải khác nhau.")
    peers = VNContractAmendment._base_manager.filter(
        company_id=company_id, contract_id=amendment.contract_id, status="approved"
    ).exclude(pk=amendment.pk)
    for peer in peers:
        if (
            (peer.effective_to is None or peer.effective_to >= amendment.effective_from)
            and (amendment.effective_to is None or peer.effective_from <= amendment.effective_to)
        ):
            raise ValidationError("Có phụ lục được duyệt chồng khoảng hiệu lực.")
    amendment.status = "approved"
    amendment.approved_by = actor
    amendment.approved_at = timezone.now()
    with allow_hr_approval():
        amendment.save()
    return amendment

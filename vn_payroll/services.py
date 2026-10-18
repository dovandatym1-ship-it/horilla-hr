"""Permission-checked, effective-dated operations for Vietnam payroll formulas.

Only handles configuration and preview. Does not issue payslips or move money.
Every operation receives an explicit company_id; no implicit session scoping.
"""

from datetime import date

from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction
from django.utils import timezone

from base.auth_backends import (
    get_allowed_company_ids,
    get_effective_permission_codenames,
)
from base.models import Company
from .models import FormulaRule
from .approval_guard import allow_approval_transition


def require_permission(actor, company_id, codename):
    """Fail closed when either the company assignment or capability is missing."""
    if not getattr(actor, "is_authenticated", False) or not actor.is_active:
        raise PermissionDenied("Vui lòng đăng nhập bằng tài khoản còn hiệu lực.")
    if not isinstance(company_id, int) or isinstance(company_id, bool):
        raise PermissionDenied("Mã công ty không hợp lệ.")
    if actor.is_superuser:
        return
    if company_id not in get_allowed_company_ids(actor):
        raise PermissionDenied("Không có quyền đối với công ty đã chọn.")
    permissions = get_effective_permission_codenames(actor, company_id=company_id)
    if codename not in permissions:
        raise PermissionDenied("Không có quyền thực hiện thao tác này.")


def _load_rule(rule_id, company_id, *, lock=False):
    qs = FormulaRule._base_manager.filter(pk=rule_id, company_id=company_id)
    if lock:
        qs = qs.select_for_update()
    return qs.get()


@transaction.atomic
def submit_for_review(rule_id, company_id, actor):
    require_permission(actor, company_id, "change_formularule")
    rule = _load_rule(rule_id, company_id, lock=True)
    if rule.status != "draft":
        raise ValidationError("Chỉ bản nháp mới được gửi duyệt.")
    if rule.created_by_id is None:
        rule.created_by = actor
    rule.status = "review"
    rule.save()
    return rule


@transaction.atomic
def approve_rule(rule_id, company_id, actor):
    require_permission(actor, company_id, "approve_formularule")
    # Serialize approvals per company to avoid concurrent overlapping rules.
    Company.objects.select_for_update().get(pk=company_id)
    rule = _load_rule(rule_id, company_id, lock=True)
    if rule.status != "review":
        raise ValidationError("Quy tắc phải ở trạng thái chờ duyệt.")
    if rule.created_by_id is None or rule.created_by_id == actor.pk:
        raise PermissionDenied("Người lập và người duyệt phải khác nhau.")
    rule.status = "approved"
    rule.approved_by = actor
    rule.approved_at = timezone.now()
    with allow_approval_transition():
        rule.save()
    return rule


@transaction.atomic
def retire_rule(rule_id, company_id, actor):
    require_permission(actor, company_id, "approve_formularule")
    rule = _load_rule(rule_id, company_id, lock=True)
    if rule.status != "approved":
        raise ValidationError("Chỉ quy tắc đang duyệt mới được ngừng áp dụng.")
    rule.status = "retired"
    with allow_approval_transition():
        rule.save()
    return rule


@transaction.atomic
def create_next_version(rule_id, company_id, actor, effective_from):
    require_permission(actor, company_id, "add_formularule")
    if not isinstance(effective_from, date):
        raise ValidationError("Ngày hiệu lực không hợp lệ.")
    Company.objects.select_for_update().get(pk=company_id)
    source = _load_rule(rule_id, company_id, lock=True)
    if source.status not in ("approved", "retired"):
        raise ValidationError("Chỉ được tạo phiên bản mới từ quy tắc đã duyệt.")
    latest = (
        FormulaRule._base_manager.filter(company_id=company_id, code=source.code)
        .order_by("-version")
        .first()
    )
    next_version = (latest.version if latest else source.version) + 1
    rule = FormulaRule(
        company_id=company_id,
        code=source.code,
        version=next_version,
        title=source.title,
        category=source.category,
        expression=source.expression,
        calculation_kind=source.calculation_kind,
        brackets=list(source.brackets),
        variables=list(source.variables),
        decimal_places=source.decimal_places,
        effective_from=effective_from,
        effective_to=None,
        legal_reference=source.legal_reference,
        status="draft",
        created_by=actor,
    )
    rule.save()
    return rule


def preview_rule(rule_id, company_id, actor, inputs):
    require_permission(actor, company_id, "preview_formularule")
    rule = _load_rule(rule_id, company_id)
    if not isinstance(inputs, dict) or set(inputs) != set(rule.variables):
        raise ValidationError("Biến đầu vào phải khớp chính xác danh sách khai báo.")
    result = rule.calculate_preview(inputs)
    return {
        "rule_id": rule.pk,
        "company_id": rule.company_id,
        "code": rule.code,
        "version": rule.version,
        "status": rule.status,
        "result": result,
        "currency": "VND",
        "inputs": dict(inputs),
        "rule_expression": rule.expression,
    }

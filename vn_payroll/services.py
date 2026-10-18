"""Controlled payroll rule preview and date-specific approved resolution."""

from datetime import date

from django.core.exceptions import ValidationError
from django.db import transaction

from vn_payroll.engine import FormulaError, calculate_lines
from vn_payroll.models import VNRuleSet


def preview_ruleset(rule_set, inputs, *, require_approved=False):
    """No database write, payslip update, or payment is performed.

    Inputs cannot override centrally approved policy parameters.
    Avoid sending confidential salary inputs to access logs.
    """
    if require_approved and rule_set.status != "approved":
        raise ValidationError("Chưa được phép dùng bộ công thức chưa phê duyệt.")
    if not isinstance(inputs, dict):
        raise ValidationError("Đầu vào phải là một đối tượng JSON.")
    overrides = set(inputs).intersection(rule_set.parameters)
    if overrides:
        raise ValidationError(f"Không được ghi đè tham số chính sách: {sorted(overrides)}")
    rules = list(rule_set.lines.order_by("position", "pk").values(
        "code", "category", "expression", "label"
    ))
    if not rules:
        raise ValidationError("Bộ công thức chưa có dòng tính nào.")
    try:
        lines, context = calculate_lines(rules, {**inputs, **rule_set.parameters})
    except FormulaError as exc:
        raise ValidationError(f"Tính thử thất bại: {exc}") from exc
    for item, meta in zip(lines, rules):
        item["label"] = meta["label"]
    return {
        "rule_set_id": rule_set.pk,
        "rule_version": rule_set.version,
        "effective_from": rule_set.effective_from.isoformat(),
        "status": rule_set.status,
        "lines": lines,
    }


def approved_ruleset_for(company_id, code, as_of):
    """Fail closed if no exactly-one approved, effective rule set exists."""
    if not isinstance(as_of, date):
        raise ValidationError("Ngày áp dụng không hợp lệ.")
    found = list(VNRuleSet.objects.filter(
        company_id=company_id,
        code=code,
        status="approved",
        effective_from__lte=as_of,
    ).filter(
        __import__("django").db.models.Q(effective_to__isnull=True)
        | __import__("django").db.models.Q(effective_to__gte=as_of)
    )[:2])
    if len(found) != 1:
        raise ValidationError("Không tìm thấy đúng một bộ công thức đã duyệt có hiệu lực.")
    return found[0]

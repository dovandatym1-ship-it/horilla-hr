"""Read-only adapter for comparing configured formulas to Horilla payroll output.

No writes to Payslip, Contract, Attendance or PayrollBatch. It explicitly
receives data returned by the existing payroll engine, rather than invoking
payroll_calculation() with hidden side-effects inside a template or request.
"""

from datetime import date
from decimal import Decimal, InvalidOperation
from hashlib import sha256
import json

from django.core.exceptions import ValidationError
from django.db.models import Q

from .models import FormulaRule
from .services import preview_rule, require_permission


# Exact keys supplied by payroll/methods/payroll_run.py.
HORILLA_NUMERIC_INPUTS = frozenset(
    (
        "contract_wage",
        "basic_pay",
        "gross_pay",
        "taxable_gross_pay",
        "net_pay",
        "paid_days",
        "unpaid_days",
        "working_days",
        "total_deductions",
        "loss_of_pay",
        "partial_pay_days",
    )
)


def rule_for_date(*, company_id, code, effective_on):
    """One and only one approved rule for a company, code and effective date."""
    if not isinstance(effective_on, date):
        raise ValidationError("Ngày áp dụng quy tắc không hợp lệ.")
    rules = list(
        FormulaRule._base_manager.filter(
            company_id=company_id,
            code=code,
            status="approved",
            effective_from__lte=effective_on,
        )
        .filter(Q(effective_to__isnull=True) | Q(effective_to__gte=effective_on))
        .order_by("-version")[:2]
    )
    if len(rules) != 1:
        raise ValidationError("Không tìm được đúng một quy tắc đã duyệt cho kỳ tính.")
    return rules[0]


def preview_from_horilla(
    *, company_id, code, effective_on, actor, payroll_data, extra_inputs=None
):
    """Calculate a traceable preview from a sanitized Horilla payroll payload.

    Existing Horilla monetary fields are floats. Stringify them at the bridge
    boundary, then use Decimal inside the VN rule evaluator. This does not
    eliminate rounding already performed by Horilla's original float engine.
    """
    require_permission(actor, company_id, "preview_formularule")
    if not isinstance(payroll_data, dict):
        raise ValidationError("Dữ liệu bảng lương đầu vào không hợp lệ.")
    rule = rule_for_date(
        company_id=company_id, code=code, effective_on=effective_on
    )
    extra_inputs = extra_inputs or {}
    if not isinstance(extra_inputs, dict):
        raise ValidationError("Biến bổ sung phải là một mapping.")
    if set(extra_inputs) & HORILLA_NUMERIC_INPUTS:
        raise ValidationError("Không được ghi đè biến lấy từ nguồn tính Horilla.")
    inputs = {}
    for name in rule.variables:
        if name in HORILLA_NUMERIC_INPUTS:
            raw = payroll_data.get(name)
        elif name in extra_inputs:
            raw = extra_inputs[name]
        else:
            raise ValidationError("Thiếu biến đầu vào đã khai báo: " + name)
        if isinstance(raw, bool) or raw is None:
            raise ValidationError("Giá trị biến không hợp lệ: " + name)
        if not isinstance(raw, (int, float, str, Decimal)):
            raise ValidationError("Biến phải là số: " + name)
        try:
            number = Decimal(str(raw))
        except (ValueError, InvalidOperation) as exc:
            raise ValidationError("Không thể chuyển biến sang số: " + name) from exc
        if not number.is_finite():
            raise ValidationError("Biến không hữu hạn: " + name)
        inputs[name] = str(number)
    if set(extra_inputs) - set(rule.variables):
        raise ValidationError("Có biến bổ sung không được khai báo.")
    preview = preview_rule(rule.pk, company_id, actor, inputs)
    fingerprint = json.dumps(
        {
            "company_id": company_id,
            "code": rule.code,
            "version": rule.version,
            "effective_on": effective_on.isoformat(),
            "expression": rule.expression,
            "inputs": inputs,
        },
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )
    preview["effective_on"] = effective_on
    preview["input_sha256"] = sha256(fingerprint.encode("utf-8")).hexdigest()
    preview["source"] = "horilla_payroll_calculation_preview"
    return preview

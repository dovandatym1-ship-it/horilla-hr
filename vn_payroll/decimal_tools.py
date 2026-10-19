"""Exact Decimal utilities for Vietnam payroll boundary calculations.

These functions never accept binary floating-point computations internally.
Legacy Horilla FloatField values are string-converted at the input boundary;
this CANNOT reverse precision already lost by the legacy engine.
"""

from decimal import Decimal, InvalidOperation, ROUND_HALF_UP

from django.core.exceptions import ValidationError


def as_decimal(value, *, field="Giá trị"):
    if value is None or isinstance(value, bool) or not isinstance(
        value, (str, int, float, Decimal)
    ):
        raise ValidationError(f"{field}: cần giá trị số hợp lệ.")
    try:
        result = Decimal(str(value))
    except (InvalidOperation, ValueError) as exc:
        raise ValidationError(f"{field}: không thể chuyển thành Decimal.") from exc
    if not result.is_finite():
        raise ValidationError(f"{field}: giá trị không hữu hạn.")
    return result


def vnd(value):
    """Round VND to whole dong, with an explicit financial rounding mode."""
    return as_decimal(value, field="Tiền VND").quantize(
        Decimal("1"), rounding=ROUND_HALF_UP
    )


def percentage(*, base, rate_percent, ceiling=None):
    """Compute a policy-supplied rate, WITHOUT embedding statutory percentages.

    ceiling is a maximum contribution BASE, not a maximum deduction.
    Rate, ceiling and taxable base must come from a separately approved,
    effective-dated employer policy. No legal correctness is implied here.
    """
    amount = as_decimal(base, field="Cơ sở đóng")
    rate = as_decimal(rate_percent, field="Tỷ lệ phần trăm")
    if amount < 0 or not Decimal("0") <= rate <= Decimal("100"):
        raise ValidationError("Cơ sở đóng hoặc tỷ lệ đóng không hợp lệ.")
    if ceiling is not None:
        cap = as_decimal(ceiling, field="Trần cơ sở đóng")
        if cap < 0:
            raise ValidationError("Trần cơ sở đóng không thể âm.")
        amount = min(amount, cap)
    return vnd(amount * rate / Decimal("100"))

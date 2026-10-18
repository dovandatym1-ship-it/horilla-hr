"""Configurable progressive tiers, using Decimal only.

Bracket boundaries and percentages come from an approved rule version.
No tax law parameters are hard-coded here.
"""

from decimal import Decimal, InvalidOperation, ROUND_HALF_UP

from .expression import InvalidFormula, _decimal


def validate_brackets(brackets):
    if not isinstance(brackets, list) or not 1 <= len(brackets) <= 20:
        raise InvalidFormula("Phải có từ 1 đến 20 bậc.")
    previous_upper = Decimal("0")
    normalized = []
    for index, row in enumerate(brackets):
        if not isinstance(row, dict) or set(row) != {"up_to", "rate_percent"}:
            raise InvalidFormula("Mỗi bậc cần up_to và rate_percent.")
        upper = row["up_to"]
        if upper is not None:
            upper = _decimal(upper)
            if upper <= previous_upper:
                raise InvalidFormula("Ngưỡng bậc phải tăng dần.")
        elif index != len(brackets) - 1:
            raise InvalidFormula("Chỉ bậc cuối được phép không có giới hạn.")
        rate = _decimal(row["rate_percent"])
        if rate < 0 or rate > 100:
            raise InvalidFormula("Thuế suất/tỷ lệ phải trong khoảng 0–100.")
        normalized.append((previous_upper, upper, rate))
        if upper is not None:
            previous_upper = upper
    if normalized[-1][1] is not None:
        raise InvalidFormula("Bậc cuối phải không có giới hạn.")
    return normalized


def progressive_amount(base, brackets, *, places=0):
    tiers = validate_brackets(brackets)
    amount = max(_decimal(base), Decimal("0"))
    if isinstance(places, bool) or not isinstance(places, int) or not 0 <= places <= 6:
        raise InvalidFormula("Độ chính xác thập phân không hợp lệ.")
    total = Decimal("0")
    for floor, ceiling, percent in tiers:
        if amount <= floor:
            break
        taxable = amount - floor if ceiling is None else min(amount, ceiling) - floor
        total += taxable * percent / Decimal("100")
    try:
        return total.quantize(Decimal("1").scaleb(-places), rounding=ROUND_HALF_UP)
    except InvalidOperation as exc:
        raise InvalidFormula("Không thể làm tròn kết quả.") from exc

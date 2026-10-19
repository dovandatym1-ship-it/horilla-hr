"""2026 VN standard employee insurance contribution: isolated golden reference.

This is NOT an eligibility engine, agency filing or payline. Caller must first
validate worker group, legal wage base, distinct ceilings, exemptions and month.
Sources: Law 41/2024/QH15, decree 188/2025/ND-CP, Employment Law 74/2025/QH15
and BHXH Viet Nam guidance for standard Vietnamese employees.
"""
from datetime import date
from decimal import Decimal

from django.core.exceptions import ValidationError

from .decimal_tools import as_decimal, percentage

SOURCE_LAW = (
    "41/2024/QH15; 188/2025/ND-CP; 74/2025/QH15; "
    "BHXH Việt Nam (lao động Việt Nam tiêu chuẩn)"
)

# Each rate is data of the reference package, never an irrevocable engine rate.
RATES = {
    "employee_social": Decimal("8"),
    "employee_health": Decimal("1.5"),
    "employee_unemployment": Decimal("1"),
    "employer_social": Decimal("17"),
    "employer_occupational": Decimal("0.5"),
    "employer_health": Decimal("3"),
    "employer_unemployment": Decimal("1"),
}


def standard_contributions_2026(
    *, effective_on, vietnamese_standard_employee,
    social_base, health_base, unemployment_base,
):
    """Calculate reference amounts from already-capped, verified salary bases.

    `vietnamese_standard_employee` is an explicit eligibility assertion,
    not something inferred from nationality alone. All bases refer to
    the same completed month and have already had legal caps/floors applied.
    """
    if (
        not isinstance(effective_on, date)
        or effective_on.year != 2026
        or vietnamese_standard_employee is not True
    ):
        raise ValidationError("Bộ tỷ lệ này chỉ dùng đối soát lao động VN tiêu chuẩn năm 2026.")
    bases = {
        "social": as_decimal(social_base, field="Căn cứ BHXH"),
        "health": as_decimal(health_base, field="Căn cứ BHYT"),
        "unemployment": as_decimal(unemployment_base, field="Căn cứ BHTN"),
    }
    if any(value < 0 for value in bases.values()):
        raise ValidationError("Căn cứ đóng không thể âm.")
    amounts = {
        name: percentage(
            base=bases[
                "social" if name.endswith(("social", "occupational"))
                else "health" if name.endswith("health") else "unemployment"
            ],
            rate_percent=rate,
        )
        for name, rate in RATES.items()
    }
    employee_total = sum(
        (value for name, value in amounts.items() if name.startswith("employee_")),
        Decimal("0"),
    )
    employer_total = sum(
        (value for name, value in amounts.items() if name.startswith("employer_")),
        Decimal("0"),
    )
    return {
        "employee": {k: v for k, v in amounts.items() if k.startswith("employee_")},
        "employer": {k: v for k, v in amounts.items() if k.startswith("employer_")},
        "employee_total_vnd": employee_total,
        "employer_total_vnd": employer_total,
        "source": SOURCE_LAW,
        "mode": "REFERENCE_ONLY_NOT_FOR_WITHHOLDING_OR_AGENCY_SUBMISSION",
    }

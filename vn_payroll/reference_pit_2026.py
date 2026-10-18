"""2026 Vietnamese resident monthly salary PIT: independent reference vectors.

Legal basis: 109/2025/QH15, consolidated 112/VBHN-VPQH dated 20 May 2026.
Wage income provisions apply to tax year 2026. This calculator is NOT a
withholding/filing integration: eligibility, exemptions, deductible insurance,
other allowed relief and dependent verification remain upstream responsibilities.

Do not execute this from payslip save; deploy only after tax specialist review.
"""
from datetime import date
from decimal import Decimal

from django.core.exceptions import ValidationError

from .brackets import progressive_amount
from .decimal_tools import as_decimal, vnd

LEGAL_SOURCE = "112/VBHN-VPQH (20/05/2026); 109/2025/QH15; 09/2026/QH16"
LEGAL_URL = "https://thuvienphapluat.vn/van-ban/Thue-Phi-Le-Phi/Van-ban-hop-nhat-112-VBHN-VPQH-2026-Luat-Thue-thu-nhap-ca-nhan-706726.aspx"
YEAR = 2026
SELF_DEDUCTION_VND = Decimal("15500000")
DEPENDENT_DEDUCTION_VND = Decimal("6200000")
MONTHLY_BRACKETS = (
    {"up_to": "10000000", "rate_percent": "5"},
    {"up_to": "30000000", "rate_percent": "10"},
    {"up_to": "60000000", "rate_percent": "20"},
    {"up_to": "100000000", "rate_percent": "30"},
    {"up_to": None, "rate_percent": "35"},
)


def resident_monthly_salary_pit(
    *, tax_year, tax_residency, taxable_salary_before_deductions, compulsory_insurance,
    verified_dependents, other_approved_deductions="0",
):
    """Return pure Decimal calculation, requiring explicit 2026 residency scope.

    `taxable_salary_before_deductions` MUST already exclude non-taxable
    allowances/reimbursements. Do not infer this from Horilla gross_pay.
    `other_approved_deductions` only after independent supporting evidence.
    Tax residency must be explicitly supplied by verified HR legal records.
    """
    if tax_residency != "resident":
        raise ValidationError(
            "Bộ thuế lũy tiến này chỉ áp dụng cá nhân cư trú; "
            "không được suy diễn thuế cho cá nhân không cư trú."
        )
    if tax_year != YEAR or isinstance(tax_year, bool):
        raise ValidationError("Bộ tham chiếu chỉ áp dụng kỳ tính thuế 2026.")
    if not isinstance(verified_dependents, int) or isinstance(verified_dependents, bool):
        raise ValidationError("Số người phụ thuộc xác minh phải là số nguyên.")
    if verified_dependents < 0:
        raise ValidationError("Số người phụ thuộc không được âm.")
    salary = as_decimal(taxable_salary_before_deductions, field="Thu nhập tính giảm trừ")
    insurance = as_decimal(compulsory_insurance, field="Bảo hiểm bắt buộc được trừ")
    other = as_decimal(other_approved_deductions, field="Giảm trừ khác được duyệt")
    if salary < 0 or insurance < 0 or other < 0:
        raise ValidationError("Thu nhập và các khoản giảm trừ không thể âm.")
    relief = SELF_DEDUCTION_VND + DEPENDENT_DEDUCTION_VND * verified_dependents
    assessable = max(Decimal("0"), salary - insurance - other - relief)
    calculated = progressive_amount(
        assessable, list(MONTHLY_BRACKETS), places=0
    )
    return {
        "tax_year": YEAR,
        "taxable_base_vnd": vnd(assessable),
        "resident_pit_vnd": calculated,
        "self_deduction_vnd": SELF_DEDUCTION_VND,
        "dependent_deduction_vnd": DEPENDENT_DEDUCTION_VND * verified_dependents,
        "legal_reference": LEGAL_SOURCE,
        "mode": "REFERENCE_ONLY_NOT_FOR_PAYSLIP_OR_TAX_FILING",
    }

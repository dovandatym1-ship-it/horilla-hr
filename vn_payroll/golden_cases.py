"""Independent numerical reconciliation for an effective-dated approved policy.

An organization supplies externally reviewed scenario inputs and expected
results. This helper verifies computations; it NEVER substitutes for legal
review or marks a tax/insurance regime legally correct.
"""

from datetime import date
from decimal import Decimal, ROUND_HALF_UP
from hashlib import sha256
import json

from django.core.exceptions import ValidationError

from .bridge import rule_for_date
from .decimal_tools import as_decimal
from .services import require_permission


def verify_policy_cases(
    *, actor, company_id, code, effective_on, cases, min_cases=3
):
    """Check distinct golden vectors for a single approved version.

    Mandatory approved rule and effective date; tax/insurance rules additionally
    require a nonempty legal reference. No real identity or pay amounts are
    written to audit tables; inputs are only included in the returned digest.
    """
    require_permission(actor, company_id, "preview_formularule")
    if not isinstance(effective_on, date):
        raise ValidationError("Ngày kiểm thử quy tắc không hợp lệ.")
    if not isinstance(min_cases, int) or isinstance(min_cases, bool) or min_cases < 3:
        raise ValidationError("Mức tối thiểu là ba ca kiểm thử.")
    if not isinstance(cases, list) or len(cases) < min_cases:
        raise ValidationError("Cần đủ ca kiểm thử độc lập trước khi nghiệm thu.")
    rule = rule_for_date(
        company_id=company_id, code=code, effective_on=effective_on
    )
    if rule.category in ("tax", "insurance") and not rule.legal_reference.strip():
        raise ValidationError("Quy tắc thuế/BH cần ghi nguồn pháp lý và hiệu lực.")
    quantum = Decimal("1").scaleb(-rule.decimal_places)
    bad_indices = []
    fingerprints = set()
    fingerprint_rows = []
    for index, case in enumerate(cases):
        if not isinstance(case, dict) or set(case) != {"inputs", "expected"}:
            raise ValidationError("Ca kiểm thử phải có inputs và expected.")
        inputs = case["inputs"]
        if not isinstance(inputs, dict) or set(inputs) != set(rule.variables):
            raise ValidationError("Biến của ca kiểm thử không khớp cấu hình.")
        clean = {
            key: str(as_decimal(inputs[key], field=key))
            for key in sorted(inputs)
        }
        serialized = json.dumps(clean, sort_keys=True, separators=(",", ":"))
        if serialized in fingerprints:
            raise ValidationError("Các ca kiểm thử phải có đầu vào khác nhau.")
        fingerprints.add(serialized)
        expected = as_decimal(case["expected"], field="Kết quả chuẩn").quantize(
            quantum, rounding=ROUND_HALF_UP
        )
        actual = rule.calculate_preview(clean)
        if actual != expected:
            bad_indices.append(index + 1)
        fingerprint_rows.append({"inputs": clean, "expected": str(expected)})
    digest = sha256(json.dumps(
        {
            "company_id": company_id, "rule_id": rule.pk,
            "version": rule.version, "effective_on": effective_on.isoformat(),
            "legal_reference": rule.legal_reference,
            "cases": fingerprint_rows,
        },
        ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")).hexdigest()
    return {
        "passed": not bad_indices,
        "tested": len(cases),
        "failed_case_numbers": bad_indices,
        "code": rule.code,
        "version": rule.version,
        "cases_sha256": digest,
        "purpose": "INDEPENDENT_NUMERICAL_VERIFICATION_ONLY",
    }

"""Idempotent, immutable Vietnam payroll reconciliation records.

This intentionally DOES NOT update Horilla Payslip, PayrollBatch, tax withholding,
bank files or any payment API. A reviewer must separately attest a payment run.
"""
from hashlib import sha256
import json

from django.core.exceptions import ValidationError
from django.db import transaction

from base.models import Company
from vn_hrm.payroll_sources import preview_with_hrm_sources
from .decimal_tools import as_decimal
from .models import FormulaRule, VNPayrollReconciliationSnapshot
from .services import require_permission


@transaction.atomic
def record_reconciliation(
    *, actor, company_id, employee_id, contract_id,
    start_date, end_date, code, payroll_data,
):
    """Store a deterministic, scoped record of approved reconciliation inputs.

    Acquires a company lock, aligned with the VN amendment approval lock. Existing
    identical evidence returns the original row; updated evidence appends a row.
    Source facts from Horilla may still be float-based and are NOT payment-ready.
    """
    require_permission(actor, company_id, "record_vnpayrollreconciliationsnapshot")
    Company.objects.select_for_update().get(pk=company_id)
    preview = preview_with_hrm_sources(
        actor=actor, company_id=company_id, employee_id=employee_id,
        contract_id=contract_id, start_date=start_date, end_date=end_date,
        code=code, payroll_data=payroll_data,
    )
    if preview.get("mode") != "READ_ONLY_RECONCILIATION_NOT_FOR_PAYMENT":
        raise ValidationError("Chỉ được lưu kết quả đối soát không chi trả.")
    rule = FormulaRule._base_manager.get(
        pk=preview["rule_id"], company_id=company_id, status="approved",
    )
    amount = as_decimal(preview["result"], field="Kết quả đối soát")
    identity = {
        "company_id": company_id,
        "employee_id": employee_id,
        "contract_id": contract_id,
        "rule_id": rule.pk,
        "rule_version": rule.version,
        "period_start": start_date.isoformat(),
        "period_end": end_date.isoformat(),
        "source_sha256": preview["hrm_source_sha256"],
        "input_sha256": preview["input_sha256"],
        "result_exact": str(amount),
    }
    digest = sha256(json.dumps(
        identity, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")).hexdigest()
    stored = VNPayrollReconciliationSnapshot._base_manager.filter(
        company_id=company_id, record_sha256=digest,
    ).first()
    if stored is not None:
        return stored
    return VNPayrollReconciliationSnapshot._base_manager.create(
        company_id=company_id,
        employee_id=employee_id,
        contract_id=contract_id,
        rule=rule,
        actor=actor,
        period_start=start_date,
        period_end=end_date,
        source_sha256=preview["hrm_source_sha256"],
        input_sha256=preview["input_sha256"],
        record_sha256=digest,
        rule_version=rule.version,
        result_exact=amount,
    )

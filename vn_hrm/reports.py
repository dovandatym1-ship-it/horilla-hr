"""Company-scoped management report, not a statutory filing or bank export.

Intentionally aggregate-only: no names, citizen IDs, tax IDs, payslip JSON,
account numbers, individual wages or raw sensitive metadata are exported.
"""

from decimal import Decimal

from django.core.exceptions import ValidationError

from payroll.models.models import Payslip
from vn_payroll.decimal_tools import as_decimal, vnd
from .services import require_company_permission


def payroll_period_summary(*, actor, company_id, start_date, end_date):
    require_company_permission(actor, company_id, "view_vnleaveledgerevent")
    if start_date is None or end_date is None or end_date < start_date:
        raise ValidationError("Khoảng ngày báo cáo không hợp lệ.")
    rows = Payslip._base_manager.filter(
        employee_id__employee_work_info__company_id=company_id,
        start_date__gte=start_date,
        end_date__lte=end_date,
        status__in=("confirmed", "paid"),
    ).only("pk", "employee_id", "start_date", "end_date", "gross_pay", "net_pay")
    keys = set()
    gross = Decimal("0")
    net = Decimal("0")
    count = 0
    for slip in rows:
        identity = (slip.employee_id_id, slip.start_date, slip.end_date)
        if identity in keys:
            raise ValidationError("Phát hiện phiếu lương trùng nhân viên và kỳ.")
        keys.add(identity)
        gross += as_decimal(slip.gross_pay, field="Tổng thu nhập")
        net += as_decimal(slip.net_pay, field="Thực lĩnh")
        count += 1
    return {
        "company_id": company_id,
        "start_date": start_date.isoformat(),
        "end_date": end_date.isoformat(),
        "payslip_count": count,
        "gross_total_vnd": vnd(gross),
        "net_total_vnd": vnd(net),
        "currency": "VND",
        "source": "horilla_confirmed_or_paid_float_converted_to_decimal",
        "is_statutory_report": False,
    }

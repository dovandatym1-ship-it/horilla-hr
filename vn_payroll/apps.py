"""Vietnam dynamic payroll extension."""

from django.apps import AppConfig


class VNPayrollConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "vn_payroll"
    verbose_name = "Công thức tính lương Việt Nam"

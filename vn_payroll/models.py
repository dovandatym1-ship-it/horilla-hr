"""Versioned, editable business formulas.

Publishing a rule does not automatically hook it into the Horilla payslip run.
The rule calculator is opt-in and is intended for preview/reconciliation until
workflow integration and approval controls are validated.
"""

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models

from .expression import InvalidFormula, evaluate


class FormulaRule(models.Model):
    CATEGORY_CHOICES = [
        ("earning", "Thu nhập"),
        ("deduction", "Khấu trừ"),
        ("insurance", "Bảo hiểm"),
        ("tax", "Thuế"),
        ("overtime", "Làm thêm giờ"),
        ("net", "Thực lĩnh"),
    ]
    STATUS_CHOICES = [
        ("draft", "Bản nháp"),
        ("review", "Chờ duyệt"),
        ("approved", "Đã duyệt"),
        ("retired", "Ngừng áp dụng"),
    ]

    company = models.ForeignKey(
        "base.Company", on_delete=models.PROTECT, related_name="vn_formula_rules"
    )
    code = models.CharField(max_length=64)
    version = models.PositiveIntegerField(default=1)
    title = models.CharField(max_length=255)
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES)
    expression = models.TextField(max_length=1000)
    # Required variable names. Values are supplied at runtime, not stored here.
    variables = models.JSONField(default=list)
    decimal_places = models.PositiveSmallIntegerField(default=0)
    effective_from = models.DateField()
    effective_to = models.DateField(null=True, blank=True)
    legal_reference = models.TextField(blank=True)
    status = models.CharField(max_length=12, choices=STATUS_CHOICES, default="draft")
    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT,
        null=True, blank=True, related_name="approved_vn_formula_rules",
    )
    approved_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["company_id", "code", "-version"]
        constraints = [
            models.UniqueConstraint(
                fields=["company", "code", "version"],
                name="vn_formula_company_code_version_unique",
            )
        ]

    def __str__(self):
        return f"{self.code} v{self.version} ({self.company_id})"

    def clean(self):
        super().clean()
        errors = {}
        if self.effective_to and self.effective_to < self.effective_from:
            errors["effective_to"] = "Ngày kết thúc phải từ ngày bắt đầu trở đi."
        if not isinstance(self.variables, list) or not self.variables or len(self.variables) > 100:
            errors["variables"] = "Khai báo từ 1 đến 100 tên biến."
        elif len(self.variables) != len(set(self.variables)) or any(
            not isinstance(v, str) or not v.isidentifier() or v.startswith("_")
            for v in self.variables
        ):
            errors["variables"] = "Tên biến phải duy nhất, hợp lệ và không bắt đầu bằng _."
        if not 0 <= self.decimal_places <= 6:
            errors["decimal_places"] = "Chỉ hỗ trợ từ 0 đến 6 chữ số thập phân."
        if self.status == "approved" and (not self.approved_by_id or not self.approved_at):
            errors["status"] = "Quy tắc phải có người và thời điểm phê duyệt."
        if self.variables and isinstance(self.variables, list) and not errors:
            try:
                evaluate(
                    self.expression,
                    {name: "1" for name in self.variables},
                    places=self.decimal_places,
                )
            except (InvalidFormula, TypeError, ValueError) as exc:
                errors["expression"] = str(exc)
        if errors:
            raise ValidationError(errors)

    def calculate_preview(self, inputs):
        """Preview only. No payslip, payroll batch or payment is mutated."""
        return evaluate(self.expression, inputs, places=self.decimal_places)

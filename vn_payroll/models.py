"""Editable, versioned rulebooks for Vietnamese payroll.

The active Horilla payslip engine is NOT replaced by these tables. Production
integration must first pass legal, finance and reconciliation acceptance gates.
"""

import ast
import re
from datetime import date
from decimal import Decimal

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone

from vn_payroll.engine import FormulaError, as_decimal, validate_syntax

CODE = re.compile(r"^[a-z][a-z0-9_]*$")


def _check_parameters(values):
    if not isinstance(values, dict) or len(values) > 80:
        raise ValidationError("Tham số phải là đối tượng chứa tối đa 80 giá trị.")
    for key, number in values.items():
        if not isinstance(key, str) or not CODE.fullmatch(key):
            raise ValidationError("Mã tham số không hợp lệ.")
        if key in {"min", "max", "abs", "round_vnd"}:
            raise ValidationError("Không dùng tên hàm làm mã tham số.")
        try:
            as_decimal(number)
        except FormulaError as exc:
            raise ValidationError(f"Tham số {key}: {exc}") from exc


class VNRuleSet(models.Model):
    """One version of a company-owned payroll rulebook."""

    STATUS = [
        ("draft", "Nháp"),
        ("review", "Chờ duyệt"),
        ("approved", "Đã duyệt"),
        ("retired", "Ngừng áp dụng"),
    ]
    company = models.ForeignKey(
        "base.Company", on_delete=models.PROTECT, related_name="vn_payroll_rule_sets"
    )
    code = models.SlugField(max_length=64)
    version = models.PositiveIntegerField(default=1)
    title = models.CharField(max_length=200)
    status = models.CharField(max_length=12, choices=STATUS, default="draft")
    effective_from = models.DateField()
    effective_to = models.DateField(null=True, blank=True)
    legal_reference = models.TextField(blank=True)
    parameters = models.JSONField(default=dict, blank=True)
    input_names = models.JSONField(default=list, blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True,
        on_delete=models.PROTECT, related_name="+"
    )
    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True,
        on_delete=models.PROTECT, related_name="+"
    )
    approved_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("company_id", "code", "-version")
        constraints = [
            models.UniqueConstraint(
                fields=("company", "code", "version"),
                name="vn_payroll_ruleset_version_unique",
            )
        ]
        permissions = [
            ("approve_vn_ruleset", "Có quyền duyệt cấu hình lương Việt Nam"),
        ]
        verbose_name = "Bộ công thức lương Việt Nam"
        verbose_name_plural = "Bộ công thức lương Việt Nam"

    def __str__(self):
        return f"{self.company_id}: {self.code} v{self.version} ({self.status})"

    def clean(self):
        super().clean()
        if self.effective_to and self.effective_to < self.effective_from:
            raise ValidationError("Ngày hết hiệu lực phải sau ngày bắt đầu.")
        _check_parameters(self.parameters)
        if not isinstance(self.input_names, list) or len(self.input_names) > 80:
            raise ValidationError("Danh sách biến đầu vào phải chứa tối đa 80 tên.")
        if len(set(self.input_names)) != len(self.input_names):
            raise ValidationError("Biến đầu vào không được trùng nhau.")
        reserved = set(self.parameters) | {"min", "max", "abs", "round_vnd"}
        if any(
            not isinstance(name, str) or not CODE.fullmatch(name) or name in reserved
            for name in self.input_names
        ):
            raise ValidationError("Biến đầu vào phải viết thường và không trùng tham số/hàm.")
        if self.status == "approved":
            if not self.approved_by_id or not self.approved_at or not self.legal_reference.strip():
                raise ValidationError("Phải có người duyệt, ngày duyệt và căn cứ chính sách/pháp lý.")
            # Distinct approved versions may not overlap for the same topic.
            existing = VNRuleSet.objects.filter(
                company_id=self.company_id, code=self.code, status="approved"
            ).exclude(pk=self.pk)
            for prior in existing.only("effective_from", "effective_to"):
                if (self.effective_to is None or prior.effective_from <= self.effective_to) and (
                    prior.effective_to is None or prior.effective_to >= self.effective_from
                ):
                    raise ValidationError("Bộ quy tắc đã duyệt bị chồng khoảng hiệu lực.")

    def save(self, *args, **kwargs):
        if self.pk:
            old = VNRuleSet.objects.get(pk=self.pk)
            if old.status == "approved":
                # Permit retirement only; never overwrite approved evidence.
                immutable = (
                    "company_id", "code", "version", "title", "effective_from",
                    "effective_to", "legal_reference", "parameters", "input_names",
                    "created_by_id", "approved_by_id", "approved_at",
                )
                if any(getattr(old, key) != getattr(self, key) for key in immutable):
                    raise ValidationError("Không được sửa nội dung bộ quy tắc đã duyệt.")
                if self.status not in ("approved", "retired"):
                    raise ValidationError("Bộ đã duyệt chỉ có thể chuyển sang Ngừng áp dụng.")
            if old.status == "retired":
                raise ValidationError("Không thể chỉnh sửa bộ công thức đã ngừng áp dụng.")
        self.full_clean()
        return super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        if self.status in ("approved", "retired"):
            raise ValidationError("Bộ đã duyệt phải được lưu lịch sử, không được xóa.")
        return super().delete(*args, **kwargs)

    def validate_rule_dependencies(self):
        """Reject unknown variables, forward references and invalid rule ordering."""
        known = set(self.parameters) | set(self.input_names)
        for line in self.lines.order_by("position", "pk"):
            if line.code in known:
                raise ValidationError("Mã dòng trùng tên biến đầu vào/tham số: " + line.code)
            try:
                parsed = validate_syntax(line.expression)
            except FormulaError as exc:
                raise ValidationError(f"Công thức {line.code}: {exc}") from exc
            referenced = {
                node.id for node in ast.walk(parsed) if isinstance(node, ast.Name)
            } - {"min", "max", "abs", "round_vnd"}
            missing = referenced - known
            if missing:
                raise ValidationError(
                    f"Công thức {line.code} có biến chưa khai báo/tính: {sorted(missing)}"
                )
            known.add(line.code)

    def approve(self, approver):
        if self.status != "review":
            raise ValidationError("Chỉ phê duyệt cấu hình ở trạng thái Chờ duyệt.")
        if not approver or not approver.is_authenticated:
            raise ValidationError("Người phê duyệt không hợp lệ.")
        if self.created_by_id == approver.pk:
            raise ValidationError("Người lập không được tự phê duyệt.")
        if not self.lines.exists():
            raise ValidationError("Bộ quy tắc không có công thức.")
        self.approved_by = approver
        self.approved_at = timezone.now()
        self.status = "approved"
        self.save()


class VNPayRule(models.Model):
    CATEGORY = [
        ("earning", "Thu nhập"),
        ("subtotal", "Tổng trung gian"),
        ("tax", "Thuế TNCN"),
        ("insurance_employee", "Bảo hiểm NLĐ"),
        ("insurance_employer", "Bảo hiểm doanh nghiệp"),
        ("deduction", "Khấu trừ khác"),
        ("net", "Thực lĩnh"),
    ]
    rule_set = models.ForeignKey(
        VNRuleSet, on_delete=models.CASCADE, related_name="lines"
    )
    position = models.PositiveIntegerField(default=10)
    code = models.SlugField(max_length=64)
    label = models.CharField(max_length=200)
    category = models.CharField(max_length=24, choices=CATEGORY)
    expression = models.CharField(max_length=700)
    explanation = models.TextField(blank=True)

    class Meta:
        ordering = ("position", "pk")
        constraints = [
            models.UniqueConstraint(
                fields=("rule_set", "code"), name="vn_payrule_code_unique"
            ),
            models.UniqueConstraint(
                fields=("rule_set", "position"), name="vn_payrule_position_unique"
            ),
        ]
        verbose_name = "Dòng công thức động"
        verbose_name_plural = "Các dòng công thức động"

    def __str__(self):
        return f"{self.code} = {self.expression}"

    def clean(self):
        super().clean()
        if self.rule_set_id and self.rule_set.status != "draft":
            raise ValidationError("Chỉ sửa công thức khi bộ quy tắc ở trạng thái Nháp.")
        if not CODE.fullmatch(self.code):
            raise ValidationError("Mã dòng công thức phải viết thường, có dấu gạch dưới.")
        if self.code in {"min", "max", "abs", "round_vnd"}:
            raise ValidationError("Mã dòng công thức trùng tên hàm.")
        try:
            validate_syntax(self.expression)
        except FormulaError as exc:
            raise ValidationError(f"Biểu thức không hợp lệ: {exc}") from exc

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        if self.rule_set.status != "draft":
            raise ValidationError("Chỉ xóa dòng ở trạng thái Nháp.")
        return super().delete(*args, **kwargs)

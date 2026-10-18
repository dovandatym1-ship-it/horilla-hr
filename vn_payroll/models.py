"""Versioned, editable business formulas.

Publishing a rule does not automatically hook it into the Horilla payslip run.
The rule calculator is opt-in and is intended for preview/reconciliation until
workflow integration and approval controls are validated.
"""

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models, transaction
from django.core.exceptions import PermissionDenied
from base.horilla_company_manager import HorillaCompanyManager

from .expression import InvalidFormula, evaluate, validate_expression
from .approval_guard import approval_transition_enabled
from .brackets import progressive_amount, validate_brackets

class FormulaRuleQuerySet(models.QuerySet):
    """Forbid bulk paths which bypass clean(), approval and version history."""

    def update(self, **kwargs):
        raise PermissionDenied("Không được sửa hàng loạt quy tắc tính lương.")

    def delete(self):
        raise PermissionDenied("Chỉ được xóa từng bản nháp sau khi kiểm tra quyền.")

    def bulk_create(self, objs, **kwargs):
        raise PermissionDenied("Không hỗ trợ tạo hàng loạt công thức bỏ qua kiểm tra.")

    def bulk_update(self, objs, fields, **kwargs):
        raise PermissionDenied("Không hỗ trợ sửa hàng loạt công thức bỏ qua kiểm tra.")


FormulaRuleManager = HorillaCompanyManager.from_queryset(FormulaRuleQuerySet)


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
    calculation_kind = models.CharField(
        max_length=20,
        choices=[("expression", "Biểu thức"), ("progressive", "Lũy tiến theo bậc")],
        default="expression",
    )
    expression = models.TextField(max_length=1000, blank=True)
    brackets = models.JSONField(default=list, blank=True)
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
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT,
        null=True, blank=True, related_name="created_vn_formula_rules",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    objects = FormulaRuleManager("company")

    class Meta:
        ordering = ["company_id", "code", "-version"]
        permissions = [
            ("approve_formularule", "Can approve Vietnam payroll formulas"),
            ("preview_formularule", "Can preview Vietnam payroll formulas"),
        ]
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
        elif any(not isinstance(v, str) for v in self.variables):
            errors["variables"] = "Tên biến phải là chuỗi."
        elif len(self.variables) != len(set(self.variables)) or any(
            not v.isidentifier() or v.startswith("_") for v in self.variables
        ):
            errors["variables"] = "Tên biến phải duy nhất, hợp lệ và không bắt đầu bằng _."
        if not 0 <= self.decimal_places <= 6:
            errors["decimal_places"] = "Chỉ hỗ trợ từ 0 đến 6 chữ số thập phân."
        if self.status in ("approved", "retired") and (
            not self.approved_by_id or not self.approved_at
        ):
            errors["status"] = "Quy tắc được duyệt phải có người và thời điểm duyệt."
        if (self.approved_by_id is None) != (self.approved_at is None):
            errors["approved_at"] = "Thông tin phê duyệt phải đủ người và thời điểm."
        if self.status in ("draft", "review") and self.approved_at:
            errors["status"] = "Quy tắc chưa duyệt không thể chứa thời điểm duyệt."
        if self.variables and isinstance(self.variables, list) and not errors:
            try:
                if self.calculation_kind == "expression":
                    if self.brackets:
                        raise InvalidFormula("Biểu thức không dùng danh sách bậc.")
                    validate_expression(self.expression, self.variables)
                elif self.calculation_kind == "progressive":
                    if str(self.expression or "").strip() or len(self.variables) != 1:
                        raise InvalidFormula(
                            "Công thức lũy tiến cần đúng một biến và không có biểu thức."
                        )
                    validate_brackets(self.brackets)
                else:
                    raise InvalidFormula("Loại công thức không hợp lệ.")
            except (InvalidFormula, TypeError, ValueError) as exc:
                errors["expression"] = str(exc)
        if errors:
            raise ValidationError(errors)

    def save(self, *args, **kwargs):
        """No in-place edits to approved rules, including direct instance.save()."""
        self.full_clean()
        with transaction.atomic():
            # A company-wide lock serializes overlapping rule approvals.
            if self.status == "approved":
                from base.models import Company

                Company.objects.select_for_update().get(pk=self.company_id)
                candidates = type(self)._base_manager.filter(
                    company_id=self.company_id,
                    code=self.code,
                    status="approved",
                ).exclude(pk=self.pk)
                for other in candidates:
                    if (not other.effective_to or other.effective_to >= self.effective_from) and (
                        not self.effective_to or other.effective_from <= self.effective_to
                    ):
                        raise ValidationError("Quy tắc đã duyệt bị trùng khoảng hiệu lực.")
            if self.pk:
                previous = type(self)._base_manager.select_for_update().get(pk=self.pk)
                # Authorization must run before checking whether a direct approval
                # skips review: bypass attempts must fail closed as permission errors.
                if (
                    self.status == "approved"
                    and previous.status != "approved"
                    and not approval_transition_enabled()
                ):
                    raise PermissionDenied(
                        "Chỉ dịch vụ phê duyệt được kích hoạt công thức."
                    )
                allowed = {
                    "draft": {"draft", "review"},
                    "review": {"draft", "review", "approved"},
                    "approved": {"retired"},
                    "retired": set(),
                }
                if self.status not in allowed.get(previous.status, set()):
                    raise ValidationError("Chuyển trạng thái công thức không hợp lệ.")
                if previous.status in ("approved", "retired"):
                    before = {
                        field.attname: getattr(previous, field.attname)
                        for field in self._meta.concrete_fields
                        if field.name != "status"
                    }
                    after = {
                        field.attname: getattr(self, field.attname)
                        for field in self._meta.concrete_fields
                        if field.name != "status"
                    }
                    if before != after:
                        raise ValidationError("Quy tắc đã duyệt là bất biến; hãy tạo phiên bản mới.")
            if self.status == "approved" and not approval_transition_enabled():
                raise PermissionDenied("Chỉ dịch vụ phê duyệt được kích hoạt công thức.")
            if self.status == "retired" and not approval_transition_enabled():
                raise PermissionDenied("Chỉ dịch vụ phê duyệt được ngừng công thức.")
            return super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        with transaction.atomic():
            if self.pk:
                status = type(self)._base_manager.select_for_update().get(pk=self.pk).status
                if status != "draft":
                    raise PermissionDenied("Chỉ được xóa bản nháp chưa được duyệt.")
            return super().delete(*args, **kwargs)

    def calculate_preview(self, inputs):
        """Preview only. No payslip, payroll batch or payment is mutated."""
        if self.calculation_kind == "progressive":
            return progressive_amount(
                inputs[self.variables[0]],
                self.brackets,
                places=self.decimal_places,
            )
        return evaluate(self.expression, inputs, places=self.decimal_places)


class FormulaAuditEvent(models.Model):
    """Append-only workflow event; never includes raw payroll/PII inputs."""

    company = models.ForeignKey("base.Company", on_delete=models.PROTECT)
    rule = models.ForeignKey(
        FormulaRule, on_delete=models.PROTECT, related_name="audit_events"
    )
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT
    )
    action = models.CharField(max_length=24)
    before_status = models.CharField(max_length=12, blank=True)
    after_status = models.CharField(max_length=12)
    created_at = models.DateTimeField(auto_now_add=True)
    objects = FormulaRuleManager("company")

    class Meta:
        ordering = ["-created_at", "-pk"]

    def save(self, *args, **kwargs):
        if self.pk:
            raise PermissionDenied("Sự kiện audit không được sửa.")
        return super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise PermissionDenied("Không được xóa nhật ký quy tắc.")


class VNPayrollReconciliationSnapshot(models.Model):
    """Immutable audit evidence of one approved rule preview, NEVER a payline.

    A new source fingerprint produces a new snapshot, never rewrites historical
    calculations. No API or background job can use this row as a payment order.
    """

    company = models.ForeignKey(
        "base.Company", on_delete=models.PROTECT,
        related_name="vn_payroll_reconciliation_snapshots",
    )
    employee = models.ForeignKey(
        "employee.Employee", on_delete=models.PROTECT,
        related_name="vn_payroll_reconciliation_snapshots",
    )
    contract = models.ForeignKey(
        "payroll.Contract", on_delete=models.PROTECT,
        related_name="vn_payroll_reconciliation_snapshots",
    )
    rule = models.ForeignKey(
        FormulaRule, on_delete=models.PROTECT,
        related_name="reconciliation_snapshots",
    )
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT,
        related_name="vn_payroll_reconciliation_snapshots",
    )
    period_start = models.DateField()
    period_end = models.DateField()
    source_sha256 = models.CharField(max_length=64)
    input_sha256 = models.CharField(max_length=64)
    record_sha256 = models.CharField(max_length=64, unique=True)
    rule_version = models.PositiveIntegerField()
    result_exact = models.DecimalField(max_digits=24, decimal_places=6)
    created_at = models.DateTimeField(auto_now_add=True)
    objects = FormulaRuleManager("company")

    class Meta:
        ordering = ["-created_at", "-pk"]
        permissions = [
            ("record_vnpayrollreconciliationsnapshot",
             "Can record Vietnam payroll reconciliation evidence"),
        ]

    def clean(self):
        super().clean()
        if self.period_end and self.period_start and self.period_end < self.period_start:
            raise ValidationError("Kỳ đối soát không hợp lệ.")
        if self.rule_id and self.rule.company_id != self.company_id:
            raise ValidationError("Quy tắc đối soát thuộc pháp nhân khác.")
        if self.result_exact is not None and not self.result_exact.is_finite():
            raise ValidationError("Kết quả đối soát không hữu hạn.")
        for key in ("source_sha256", "input_sha256", "record_sha256"):
            digest = getattr(self, key)
            if not isinstance(digest, str) or len(digest) != 64 or any(
                char not in "0123456789abcdef" for char in digest
            ):
                raise ValidationError("Giá trị fingerprint không hợp lệ.")

    def save(self, *args, **kwargs):
        if self.pk:
            raise PermissionDenied("Bản đối soát bất biến; chỉ được tạo bản mới.")
        self.full_clean()
        return super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise PermissionDenied("Không được xóa chứng cứ đối soát lương.")

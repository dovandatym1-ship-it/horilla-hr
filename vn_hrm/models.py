"""Effective-dated Vietnamese HRM extensions without rewriting Horilla records."""

from django.conf import settings
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import models

from base.horilla_company_manager import HorillaCompanyManager
from .crypto import protect_identifier
from .approval_guard import hr_approval_enabled


class SensitiveNoBulkQuerySet(models.QuerySet):
    """Block ORM bulk changes that bypass validation and per-object audit."""

    def update(self, **kwargs):
        raise PermissionDenied("Không cho sửa hàng loạt bản ghi nghiệp vụ nhạy cảm.")

    def delete(self):
        raise PermissionDenied("Không cho xóa hàng loạt bản ghi nghiệp vụ nhạy cảm.")

    def bulk_create(self, objs, **kwargs):
        raise PermissionDenied("Không cho tạo hàng loạt bỏ qua validation.")

    def bulk_update(self, objs, fields, **kwargs):
        raise PermissionDenied("Không cho cập nhật hàng loạt bỏ qua validation.")


SensitiveManager = HorillaCompanyManager.from_queryset(SensitiveNoBulkQuerySet)


class VNCompanyProfile(models.Model):
    company = models.OneToOneField(
        "base.Company", on_delete=models.PROTECT, related_name="vn_legal_profile"
    )
    legal_name = models.CharField(max_length=255)
    tax_code = models.CharField(max_length=32, blank=True)
    province_code = models.CharField(max_length=20, blank=True)
    commune_code = models.CharField(max_length=20, blank=True)
    wage_zone = models.CharField(
        max_length=3, blank=True,
        choices=[("I", "Vùng I"), ("II", "Vùng II"),
                 ("III", "Vùng III"), ("IV", "Vùng IV")],
    )
    last_verified_at = models.DateTimeField(null=True, blank=True)
    objects = HorillaCompanyManager("company")

    def __str__(self):
        return self.legal_name


class VNEmployeeLegalProfile(models.Model):
    RESIDENCY_CHOICES = [
        ("unknown", "Chưa xác định"),
        ("resident", "Cư trú"),
        ("nonresident", "Không cư trú"),
    ]
    company = models.ForeignKey("base.Company", on_delete=models.PROTECT)
    employee = models.ForeignKey(
        "employee.Employee", on_delete=models.PROTECT,
        related_name="vn_legal_profiles",
    )
    nationality = models.CharField(max_length=2, default="VN")
    tax_residency = models.CharField(
        max_length=16, choices=RESIDENCY_CHOICES, default="unknown"
    )
    citizen_ciphertext = models.TextField(blank=True, editable=False)
    citizen_digest = models.CharField(
        max_length=64, blank=True, editable=False, db_index=True
    )
    tax_ciphertext = models.TextField(blank=True, editable=False)
    tax_digest = models.CharField(max_length=64, blank=True, editable=False)
    insurance_ciphertext = models.TextField(blank=True, editable=False)
    insurance_digest = models.CharField(max_length=64, blank=True, editable=False)
    updated_at = models.DateTimeField(auto_now=True)
    objects = SensitiveManager("company")

    class Meta:
        permissions = [
            ("manage_vn_identifiers", "Can set encrypted Vietnamese identifiers"),
            ("reveal_vn_identifiers", "Can reveal encrypted Vietnamese identifiers"),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=["company", "employee"], name="vn_hrm_employee_company_unique"
            ),
            models.UniqueConstraint(
                fields=["company", "citizen_digest"],
                condition=~models.Q(citizen_digest=""),
                name="vn_hrm_citizen_digest_unique",
            ),
        ]

    def set_identifier(self, kind, value):
        columns = {
            "citizen": ("citizen_ciphertext", "citizen_digest"),
            "tax": ("tax_ciphertext", "tax_digest"),
            "insurance": ("insurance_ciphertext", "insurance_digest"),
        }
        if kind not in columns:
            raise ValidationError("Loại định danh không hợp lệ.")
        ciphertext, digest = protect_identifier(value)
        setattr(self, columns[kind][0], ciphertext)
        setattr(self, columns[kind][1], digest)

    def __str__(self):
        return f"VN legal profile {self.employee_id} / {self.company_id}"

    def delete(self, *args, **kwargs):
        raise PermissionDenied("Hồ sơ pháp lý không được xóa ngoài quy trình lưu trữ.")


class VNDependent(models.Model):
    STATUS_CHOICES = [
        ("draft", "Chờ bổ sung"),
        ("verified", "Đã xác minh"),
        ("invalid", "Không hợp lệ"),
    ]
    company = models.ForeignKey("base.Company", on_delete=models.PROTECT)
    employee = models.ForeignKey(
        "employee.Employee", on_delete=models.PROTECT,
        related_name="vn_dependents",
    )
    name = models.CharField(max_length=255)
    relation = models.CharField(max_length=40)
    date_of_birth = models.DateField(null=True, blank=True)
    valid_from = models.DateField()
    valid_to = models.DateField(null=True, blank=True)
    status = models.CharField(
        max_length=10, default="draft", choices=STATUS_CHOICES
    )
    verified_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.PROTECT
    )
    objects = SensitiveManager("company")

    def clean(self):
        super().clean()
        if self.valid_to and self.valid_to < self.valid_from:
            raise ValidationError({"valid_to": "Ngày kết thúc trước ngày bắt đầu."})
        if self.status == "verified" and not self.verified_by_id:
            raise ValidationError({"status": "Cần người xác minh người phụ thuộc."})

    def save(self, *args, **kwargs):
        self.full_clean()
        if self.status == "verified" and not hr_approval_enabled():
            raise PermissionDenied("Chỉ quy trình xác minh mới được phê duyệt.")
        if self.pk:
            old = type(self)._base_manager.get(pk=self.pk)
            if old.status == "verified":
                raise PermissionDenied("Hồ sơ phụ thuộc đã duyệt không thể sửa đè.")
        return super().save(*args, **kwargs)


class VNContractAmendment(models.Model):
    STATUS_CHOICES = [
        ("draft", "Nháp"),
        ("review", "Chờ duyệt"),
        ("approved", "Đã duyệt"),
    ]
    company = models.ForeignKey("base.Company", on_delete=models.PROTECT)
    contract = models.ForeignKey(
        "payroll.Contract", on_delete=models.PROTECT, related_name="vn_amendments"
    )
    version = models.PositiveIntegerField()
    effective_from = models.DateField()
    effective_to = models.DateField(null=True, blank=True)
    wage_vnd = models.DecimalField(max_digits=20, decimal_places=0)
    reason = models.TextField(blank=True)
    status = models.CharField(
        max_length=10, choices=STATUS_CHOICES, default="draft"
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True,
        on_delete=models.PROTECT, related_name="created_vn_contract_amendments",
    )
    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True,
        on_delete=models.PROTECT, related_name="approved_vn_contract_amendments",
    )
    approved_at = models.DateTimeField(null=True, blank=True)
    objects = SensitiveManager("company")

    class Meta:
        permissions = [
            ("approve_vncontractamendment", "Can approve Vietnam contract amendments"),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=["contract", "version"], name="vn_hrm_contract_amendment_unique"
            )
        ]

    def clean(self):
        super().clean()
        if self.effective_to and self.effective_to < self.effective_from:
            raise ValidationError({"effective_to": "Khoảng hiệu lực không hợp lệ."})
        if self.wage_vnd is not None and self.wage_vnd < 0:
            raise ValidationError({"wage_vnd": "Tiền lương không thể âm."})
        if self.status == "approved":
            if not self.approved_by_id or not self.approved_at or not self.created_by_id:
                raise ValidationError("Phụ lục phải có đủ người lập và người duyệt.")
            if self.approved_by_id == self.created_by_id:
                raise ValidationError("Người duyệt và người lập phải khác nhau.")
        if self.contract_id:
            work_info = getattr(self.contract.employee_id, "employee_work_info", None)
            if work_info is not None and work_info.company_id_id != self.company_id:
                raise ValidationError("Pháp nhân khác với hợp đồng của nhân viên.")

    def save(self, *args, **kwargs):
        self.full_clean()
        if self.status == "approved" and not hr_approval_enabled():
            raise PermissionDenied("Phải duyệt phụ lục qua dịch vụ có phân quyền.")
        if self.pk:
            original = type(self)._base_manager.get(pk=self.pk)
            if original.status == "approved":
                raise PermissionDenied("Phụ lục đã duyệt không thể chỉnh sửa.")
            allowed = {"draft": ("draft", "review"), "review": ("review", "draft", "approved")}
            if self.status not in allowed.get(original.status, ()):
                raise ValidationError("Chuyển trạng thái phụ lục không hợp lệ.")
        return super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        if self.status == "approved":
            raise PermissionDenied("Không được xóa phụ lục đã duyệt.")
        return super().delete(*args, **kwargs)


class VNLeaveLedgerEvent(models.Model):
    """Signed leave adjustments; not yet connected to Horilla's LeaveRequest."""
    company = models.ForeignKey("base.Company", on_delete=models.PROTECT)
    employee = models.ForeignKey(
        "employee.Employee", on_delete=models.PROTECT,
        related_name="vn_leave_events",
    )
    source_event_key = models.CharField(max_length=100)
    event_type = models.CharField(
        max_length=16,
        choices=[
            ("accrual", "Tích lũy"), ("debit", "Trừ phép"),
            ("credit", "Hoàn phép"), ("expiry", "Hết hạn"),
            ("adjustment", "Điều chỉnh"),
        ],
    )
    units = models.DecimalField(max_digits=9, decimal_places=3)
    effective_on = models.DateField()
    reason = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.PROTECT
    )
    objects = SensitiveManager("company")

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["company", "source_event_key", "event_type"],
                name="vn_hrm_leave_event_idempotency",
            )
        ]

    def clean(self):
        super().clean()
        if self.units is None or self.units == 0:
            raise ValidationError({"units": "Giá trị số dư phép không được bằng 0."})
        if self.event_type in ("debit", "expiry") and self.units > 0:
            raise ValidationError({"units": "Sự kiện trừ/hết phép phải là số âm."})
        if self.event_type in ("accrual", "credit") and self.units < 0:
            raise ValidationError({"units": "Sự kiện cộng/hoàn phép phải là số dương."})

    def save(self, *args, **kwargs):
        self.full_clean()
        if self.pk:
            raise PermissionDenied("Nhật ký phép không thể sửa; tạo giao dịch điều chỉnh.")
        return super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise PermissionDenied("Không thể xóa sự kiện số dư phép.")


class VNSensitiveAccessAudit(models.Model):
    """Never log decrypted identifiers in audit rows."""
    company = models.ForeignKey("base.Company", on_delete=models.PROTECT)
    employee = models.ForeignKey("employee.Employee", on_delete=models.PROTECT)
    actor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    purpose = models.CharField(max_length=255)
    action = models.CharField(max_length=30)
    created_at = models.DateTimeField(auto_now_add=True)
    objects = SensitiveManager("company")

    def save(self, *args, **kwargs):
        if self.pk:
            raise PermissionDenied("Không được sửa nhật ký truy cập thông tin nhạy cảm.")
        return super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise PermissionDenied("Không được xóa nhật ký truy cập thông tin nhạy cảm.")

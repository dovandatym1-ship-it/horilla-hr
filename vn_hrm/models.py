"""Vietnam HR legal records, HR decisions and append-only leave adjustments.

Personal identity numbers MUST live in a separately controlled encrypted vault.
These models only keep masked suffixes and opaque vault references; no raw
CCCD, tax number, social insurance number, or bank numbers are accepted.
All administrative access is intentionally superuser-only until a fully
tenant-scoped HR interface and field-level policy have been implemented.
"""

import uuid
from decimal import Decimal

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone

from base.horilla_company_manager import HorillaCompanyManager


class VNEmployeeLegalProfile(models.Model):
    employee = models.OneToOneField(
        "employee.Employee", on_delete=models.PROTECT, related_name="vn_legal_profile"
    )
    company = models.ForeignKey("base.Company", on_delete=models.PROTECT)
    nationality = models.CharField(max_length=2, default="VN")
    citizen_id_suffix = models.CharField(max_length=4, blank=True)
    citizen_id_vault_ref = models.CharField(max_length=200, blank=True)
    tax_id_suffix = models.CharField(max_length=4, blank=True)
    tax_id_vault_ref = models.CharField(max_length=200, blank=True)
    social_insurance_suffix = models.CharField(max_length=4, blank=True)
    social_insurance_vault_ref = models.CharField(max_length=200, blank=True)
    residency_type = models.CharField(
        max_length=20,
        choices=[("unverified", "Chưa xác minh"), ("resident", "Cư trú"), ("nonresident", "Không cư trú")],
        default="unverified",
    )
    verification_status = models.CharField(
        max_length=20,
        choices=[("pending", "Chưa xác minh"), ("verified", "Đã xác minh")],
        default="pending",
    )
    verified_at = models.DateTimeField(null=True, blank=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    objects = HorillaCompanyManager("company")

    class Meta:
        verbose_name = "Hồ sơ pháp lý nhân viên Việt Nam"
        verbose_name_plural = "Hồ sơ pháp lý nhân viên Việt Nam"

    def clean(self):
        super().clean()
        for key in ("citizen_id_suffix", "tax_id_suffix", "social_insurance_suffix"):
            suffix = getattr(self, key)
            if suffix and (len(suffix) != 4 or not suffix.isdigit()):
                raise ValidationError({key: "Chỉ lưu bốn chữ số cuối, không nhập mã định danh đầy đủ."})
        for key in ("citizen_id_vault_ref", "tax_id_vault_ref", "social_insurance_vault_ref"):
            ref = getattr(self, key)
            if ref and (ref.isdigit() or any(ch.isspace() for ch in ref)):
                raise ValidationError({key: "Mã tham chiếu vault phải là mã opaque, không chứa dữ liệu gốc."})
        if self.employee_id and self.company_id:
            assigned = getattr(self.employee, "employee_work_info", None)
            if assigned and assigned.company_id_id and assigned.company_id_id != self.company_id:
                raise ValidationError("Pháp nhân của hồ sơ phải khớp nhân viên hiện tại. Điều chuyển cần nghiệp vụ riêng.")

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)

    def __str__(self):
        return f"Hồ sơ VN của nhân viên #{self.employee_id}"


class VNDependent(models.Model):
    employee = models.ForeignKey(
        "employee.Employee", on_delete=models.PROTECT, related_name="vn_dependents"
    )
    company = models.ForeignKey("base.Company", on_delete=models.PROTECT)
    full_name = models.CharField(max_length=200)
    relationship = models.CharField(max_length=40)
    birth_date = models.DateField(null=True, blank=True)
    identity_suffix = models.CharField(max_length=4, blank=True)
    identity_vault_ref = models.CharField(max_length=200, blank=True)
    eligible_from = models.DateField()
    eligible_to = models.DateField(null=True, blank=True)
    verification_status = models.CharField(
        max_length=20,
        choices=[("pending", "Chưa xác minh"), ("verified", "Đã xác minh"), ("rejected", "Không hợp lệ")],
        default="pending",
    )
    evidence_ref = models.CharField(max_length=200, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    objects = HorillaCompanyManager("company")

    class Meta:
        verbose_name = "Người phụ thuộc"
        verbose_name_plural = "Người phụ thuộc"

    def clean(self):
        super().clean()
        if self.eligible_to and self.eligible_to < self.eligible_from:
            raise ValidationError("Ngày hết quyền lợi phải sau ngày bắt đầu.")
        if self.identity_suffix and (len(self.identity_suffix) != 4 or not self.identity_suffix.isdigit()):
            raise ValidationError("Chỉ lưu bốn chữ số cuối của mã định danh.")
        if self.identity_vault_ref and (
            self.identity_vault_ref.isdigit() or any(ch.isspace() for ch in self.identity_vault_ref)
        ):
            raise ValidationError("Chỉ lưu mã tham chiếu kho bảo mật, không lưu số định danh.")
        if self.employee_id and self.company_id:
            assigned = getattr(self.employee, "employee_work_info", None)
            if assigned and assigned.company_id_id and assigned.company_id_id != self.company_id:
                raise ValidationError("Pháp nhân của người phụ thuộc không khớp hồ sơ nhân viên.")

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)


class VNContractAmendment(models.Model):
    company = models.ForeignKey("base.Company", on_delete=models.PROTECT)
    contract = models.ForeignKey(
        "payroll.Contract", on_delete=models.PROTECT, related_name="vn_amendments"
    )
    amendment_code = models.CharField(max_length=64)
    effective_date = models.DateField()
    new_monthly_wage_vnd = models.DecimalField(max_digits=17, decimal_places=0)
    status = models.CharField(
        max_length=20, choices=[("draft", "Nháp"), ("approved", "Đã duyệt")],
        default="draft",
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, null=True, blank=True,
        related_name="+"
    )
    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, null=True, blank=True,
        related_name="+"
    )
    approved_at = models.DateTimeField(null=True, blank=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    objects = HorillaCompanyManager("company")

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=("company", "amendment_code"),
                name="vn_contract_amendment_code_unique",
            )
        ]
        verbose_name = "Phụ lục hợp đồng Việt Nam"
        verbose_name_plural = "Phụ lục hợp đồng Việt Nam"

    def clean(self):
        super().clean()
        if self.new_monthly_wage_vnd is not None and self.new_monthly_wage_vnd < 0:
            raise ValidationError("Lương tháng mới không thể âm.")
        if self.status == "approved":
            if not self.approved_by_id or not self.approved_at:
                raise ValidationError("Phụ lục phải có người và thời điểm phê duyệt.")
            if self.created_by_id and self.created_by_id == self.approved_by_id:
                raise ValidationError("Người lập không được tự duyệt phụ lục.")
        if self.contract_id and self.company_id:
            assignment = getattr(self.contract.employee_id, "employee_work_info", None)
            if assignment and assignment.company_id_id and assignment.company_id_id != self.company_id:
                raise ValidationError("Phụ lục không thuộc pháp nhân của nhân viên.")

    def save(self, *args, **kwargs):
        if self.pk and VNContractAmendment.objects.filter(pk=self.pk, status="approved").exists():
            raise ValidationError("Phụ lục đã duyệt không được sửa đè.")
        self.full_clean()
        return super().save(*args, **kwargs)

    def approve(self, user):
        if self.status != "draft":
            raise ValidationError("Chỉ phê duyệt phụ lục đang Nháp.")
        if self.created_by_id == user.pk:
            raise ValidationError("Người lập không được tự phê duyệt.")
        self.status = "approved"
        self.approved_by = user
        self.approved_at = timezone.now()
        self.save()


class VNAttendanceCorrection(models.Model):
    company = models.ForeignKey("base.Company", on_delete=models.PROTECT)
    employee = models.ForeignKey("employee.Employee", on_delete=models.PROTECT)
    work_date = models.DateField()
    requested_minutes = models.IntegerField()
    reason = models.TextField()
    status = models.CharField(
        max_length=20,
        choices=[("pending", "Chờ duyệt"), ("approved", "Đã duyệt"), ("rejected", "Đã từ chối")],
        default="pending",
    )
    requested_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.PROTECT,
        related_name="+"
    )
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.PROTECT,
        related_name="+"
    )
    reviewed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    objects = HorillaCompanyManager("company")

    class Meta:
        verbose_name = "Đề nghị điều chỉnh chấm công"
        verbose_name_plural = "Đề nghị điều chỉnh chấm công"

    def clean(self):
        super().clean()
        if not -1440 <= self.requested_minutes <= 1440:
            raise ValidationError("Điều chỉnh công phải nằm trong giới hạn một ngày.")
        if not self.reason.strip():
            raise ValidationError("Bắt buộc ghi lý do điều chỉnh.")
        if self.status != "pending":
            if not self.reviewed_by_id or not self.reviewed_at:
                raise ValidationError("Quyết định phải có người và thời điểm duyệt.")
            if self.requested_by_id and self.requested_by_id == self.reviewed_by_id:
                raise ValidationError("Người đề nghị không được tự duyệt.")

    def save(self, *args, **kwargs):
        if self.pk and VNAttendanceCorrection.objects.filter(pk=self.pk).exclude(status="pending").exists():
            raise ValidationError("Quyết định công đã xử lý không được sửa đè.")
        self.full_clean()
        return super().save(*args, **kwargs)


class VNLeaveLedgerEntry(models.Model):
    """Standalone adjustment ledger; Horilla's AvailableLeave is NOT changed."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    company = models.ForeignKey("base.Company", on_delete=models.PROTECT)
    employee = models.ForeignKey("employee.Employee", on_delete=models.PROTECT)
    leave_type = models.ForeignKey("leave.LeaveType", on_delete=models.PROTECT)
    source_key = models.CharField(max_length=120)
    effective_date = models.DateField()
    units = models.DecimalField(max_digits=9, decimal_places=2)
    reason = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    objects = HorillaCompanyManager("company")

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=("company", "source_key"), name="vn_leave_ledger_source_unique"
            ),
        ]
        ordering = ("effective_date", "created_at")
        verbose_name = "Giao dịch số dư phép"
        verbose_name_plural = "Giao dịch số dư phép"

    def clean(self):
        super().clean()
        if self.units == Decimal("0"):
            raise ValidationError("Giao dịch phải tăng hoặc giảm phép khác 0.")
        if not self.reason.strip():
            raise ValidationError("Bắt buộc ghi lý do giao dịch phép.")

    def save(self, *args, **kwargs):
        if self.pk and VNLeaveLedgerEntry.objects.filter(pk=self.pk).exists():
            raise ValidationError("Sổ phép chỉ bổ sung giao dịch, không sửa bản ghi cũ.")
        self.full_clean()
        return super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise ValidationError("Không xóa giao dịch số dư phép; hãy thêm bút toán đảo.")

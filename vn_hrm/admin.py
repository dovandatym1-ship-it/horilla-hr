"""Restricted back-office UI for Vietnamese employee and operations records.

The initial implementation is accessible only to superusers. Ordinary HR
access requires tenant/field-scope permission checks before enabling it.
"""

from django.contrib import admin, messages
from django.core.exceptions import ValidationError
from django.utils import timezone

from vn_hrm.models import (
    VNAttendanceCorrection,
    VNContractAmendment,
    VNDependent,
    VNEmployeeLegalProfile,
    VNLeaveLedgerEntry,
)


class VNRootOnlyAdmin(admin.ModelAdmin):
    def has_module_permission(self, request):
        return bool(request.user.is_active and request.user.is_superuser)

    def has_view_permission(self, request, obj=None):
        return bool(request.user.is_active and request.user.is_superuser)

    def has_add_permission(self, request):
        return bool(request.user.is_active and request.user.is_superuser)

    def has_change_permission(self, request, obj=None):
        return bool(request.user.is_active and request.user.is_superuser)

    def has_delete_permission(self, request, obj=None):
        return bool(request.user.is_active and request.user.is_superuser)


@admin.register(VNEmployeeLegalProfile)
class EmployeeLegalAdmin(VNRootOnlyAdmin):
    list_display = ("employee", "company", "nationality", "residency_type", "verification_status", "citizen_id_suffix")
    list_filter = ("company", "residency_type", "verification_status")
    search_fields = ("employee__email", "employee__badge_id")
    # Full identifiers are never stored in this model. Vault IDs are opaque.


@admin.register(VNDependent)
class DependentAdmin(VNRootOnlyAdmin):
    list_display = ("employee", "company", "relationship", "eligible_from", "eligible_to", "verification_status")
    list_filter = ("company", "verification_status")
    search_fields = ("employee__email",)
    # Avoid indexing/searching dependent names or identifiers by default.


@admin.register(VNContractAmendment)
class ContractAmendmentAdmin(VNRootOnlyAdmin):
    list_display = ("amendment_code", "company", "contract", "effective_date", "status")
    list_filter = ("company", "status")
    readonly_fields = ("status", "created_by", "approved_by", "approved_at", "created_at")

    def save_model(self, request, obj, form, change):
        if not change:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)
    actions = ["approve_amendments"]

    def get_readonly_fields(self, request, obj=None):
        if obj and obj.status == "approved":
            return [field.name for field in obj._meta.fields]
        return super().get_readonly_fields(request, obj)

    def has_delete_permission(self, request, obj=None):
        return super().has_delete_permission(request, obj) and (
            obj is None or obj.status == "draft"
        )

    @admin.action(description="Duyệt phụ lục hợp đồng (không tự thay hợp đồng gốc)")
    def approve_amendments(self, request, queryset):
        for item in queryset:
            if item.status != "draft":
                continue
            try:
                item.approve(request.user)
                self.message_user(request, f"Đã duyệt phụ lục {item.amendment_code}.", messages.SUCCESS)
            except ValidationError as exc:
                self.message_user(request, str(exc), messages.ERROR)


@admin.register(VNAttendanceCorrection)
class AttendanceCorrectionAdmin(VNRootOnlyAdmin):
    list_display = ("employee", "company", "work_date", "requested_minutes", "status")
    list_filter = ("company", "status", "work_date")
    readonly_fields = ("status", "requested_by", "reviewed_by", "reviewed_at", "created_at")
    actions = ["approve_requests", "reject_requests"]

    def save_model(self, request, obj, form, change):
        if not change:
            obj.requested_by = request.user
        super().save_model(request, obj, form, change)

    def get_readonly_fields(self, request, obj=None):
        if obj and obj.status != "pending":
            return [field.name for field in obj._meta.fields]
        return super().get_readonly_fields(request, obj)

    def _review(self, request, queryset, status):
        for item in queryset:
            if item.status != "pending":
                continue
            item.status = status
            item.reviewed_by = request.user
            item.reviewed_at = timezone.now()
            try:
                item.save()
                self.message_user(request, f"Đã xử lý yêu cầu công #{item.pk}.", messages.SUCCESS)
            except ValidationError as exc:
                self.message_user(request, str(exc), messages.ERROR)

    @admin.action(description="Duyệt điều chỉnh công (chưa đồng bộ Attendance gốc)")
    def approve_requests(self, request, queryset):
        self._review(request, queryset, "approved")

    @admin.action(description="Từ chối điều chỉnh công")
    def reject_requests(self, request, queryset):
        self._review(request, queryset, "rejected")


@admin.register(VNLeaveLedgerEntry)
class LeaveLedgerAdmin(VNRootOnlyAdmin):
    list_display = ("employee", "company", "leave_type", "effective_date", "units", "source_key")
    list_filter = ("company", "leave_type")

    def has_change_permission(self, request, obj=None):
        return obj is None and super().has_change_permission(request, obj)

    def has_delete_permission(self, request, obj=None):
        return False

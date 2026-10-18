"""Restrictive configuration UI: personal IDs are never exposed in Django Admin."""

from django.contrib import admin
from django.core.exceptions import PermissionDenied

from .models import VNCompanyProfile, VNContractAmendment, VNDependent


class RestrictedCompanyAdmin(admin.ModelAdmin):
    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        return queryset if request.user.is_superuser else queryset.none()

    def has_add_permission(self, request):
        return request.user.is_superuser and super().has_add_permission(request)

    def has_change_permission(self, request, obj=None):
        return request.user.is_superuser and super().has_change_permission(request, obj)

    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser and super().has_delete_permission(request, obj)


@admin.register(VNCompanyProfile)
class VNCompanyProfileAdmin(RestrictedCompanyAdmin):
    list_display = ("company", "legal_name", "tax_code", "wage_zone")
    search_fields = ("company__company", "legal_name", "tax_code")


@admin.register(VNDependent)
class VNDependentAdmin(RestrictedCompanyAdmin):
    list_display = (
        "company", "employee", "name", "relation",
        "valid_from", "valid_to", "status",
    )
    list_filter = ("company", "status")
    search_fields = ("name", "employee__employee_first_name")
    readonly_fields = ("verified_by",)

    def save_model(self, request, obj, form, change):
        # A separate audited workflow is required to set Verified.
        if obj.status == "verified":
            raise PermissionDenied("Xác minh người phụ thuộc qua dịch vụ được phân quyền.")
        super().save_model(request, obj, form, change)


@admin.register(VNContractAmendment)
class VNContractAmendmentAdmin(RestrictedCompanyAdmin):
    list_display = (
        "company", "contract", "version", "wage_vnd",
        "effective_from", "effective_to", "status",
    )
    list_filter = ("company", "status")
    readonly_fields = ("status",)

    def save_model(self, request, obj, form, change):
        if change and obj.status != "draft":
            raise PermissionDenied("Phụ lục đã duyệt không được sửa.")
        if not change:
            obj.status = "draft"
        super().save_model(request, obj, form, change)

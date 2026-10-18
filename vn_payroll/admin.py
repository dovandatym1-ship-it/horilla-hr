"""Scoped Django admin for editable payroll formulas.

Admin access requires explicit permission on this model. This interface is
for configuration and preview; approving requires a separate audited workflow.
"""

from django.contrib import admin, messages
from django.core.exceptions import PermissionDenied, ValidationError

from .services import approve_rule, retire_rule, submit_for_review

from .models import FormulaRule


@admin.register(FormulaRule)
class FormulaRuleAdmin(admin.ModelAdmin):
    list_display = (
        "code", "version", "title", "company", "category", "status",
        "effective_from", "effective_to",
    )
    list_filter = ("company", "category", "status")
    search_fields = ("code", "title")
    readonly_fields = ("approved_by", "approved_at", "created_by", "created_at")
    actions = ("submit_selected", "approve_selected", "retire_selected")

    def get_readonly_fields(self, request, obj=None):
        if obj and obj.status != "draft":
            return tuple(field.name for field in obj._meta.concrete_fields)
        return self.readonly_fields


    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        if request.user.is_superuser:
            return queryset
        # No cross-company admin access is granted without a vetted
        # company-assignment integration. Non-superusers fail closed.
        return queryset.none()

    def has_add_permission(self, request):
        return request.user.is_superuser and super().has_add_permission(request)

    def has_change_permission(self, request, obj=None):
        return request.user.is_superuser and super().has_change_permission(request, obj)

    def has_delete_permission(self, request, obj=None):
        if obj is not None and obj.status != "draft":
            return False
        return request.user.is_superuser and super().has_delete_permission(request, obj)

    def save_model(self, request, obj, form, change):
        if change:
            previous = FormulaRule._base_manager.get(pk=obj.pk)
            if previous.status != "draft" or obj.status != "draft":
                raise PermissionDenied("Sử dụng hành động gửi duyệt/phê duyệt hoặc tạo phiên bản.")
        else:
            obj.status = "draft"
            obj.created_by = request.user
        super().save_model(request, obj, form, change)

    @admin.action(description="Gửi duyệt công thức đã chọn")
    def submit_selected(self, request, queryset):
        for rule in queryset:
            try:
                submit_for_review(rule.pk, rule.company_id, request.user)
            except (ValidationError, PermissionDenied) as exc:
                self.message_user(request, str(exc), messages.ERROR)

    @admin.action(description="Phê duyệt công thức đã chọn")
    def approve_selected(self, request, queryset):
        for rule in queryset:
            try:
                approve_rule(rule.pk, rule.company_id, request.user)
            except (ValidationError, PermissionDenied) as exc:
                self.message_user(request, str(exc), messages.ERROR)

    @admin.action(description="Ngừng áp dụng công thức đã chọn")
    def retire_selected(self, request, queryset):
        for rule in queryset:
            try:
                retire_rule(rule.pk, rule.company_id, request.user)
            except (ValidationError, PermissionDenied) as exc:
                self.message_user(request, str(exc), messages.ERROR)

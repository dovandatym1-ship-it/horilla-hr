"""Restricted admin UI for per-company, versioned payroll formulas.

All configuration changes are restricted to Django superusers in this MVP.
Approval requires a DIFFERENT superuser from the creator (maker/checker).
Only test inputs are accepted on preview; previews do not write payslips.
"""
import json

from django import forms
from django.contrib import admin, messages
from django.core.exceptions import ValidationError
from django.db import transaction
from django.http import HttpResponseForbidden
from django.shortcuts import get_object_or_404, render
from django.urls import path
from django.utils.html import format_html

from vn_payroll.models import VNPayRule, VNRuleSet
from vn_payroll.services import preview_ruleset


class RulePreviewForm(forms.Form):
    inputs = forms.CharField(
        label="Dữ liệu giả lập JSON (KHÔNG nhập dữ liệu lương thật)",
        widget=forms.Textarea(attrs={"rows": 9, "cols": 75}),
        initial='{"salary": "15000000", "paid_days": "22", "standard_days": "22"}',
    )

    def clean_inputs(self):
        try:
            value = json.loads(self.cleaned_data["inputs"])
        except (TypeError, json.JSONDecodeError) as exc:
            raise forms.ValidationError("JSON không hợp lệ.") from exc
        if not isinstance(value, dict):
            raise forms.ValidationError("Dữ liệu phải là đối tượng JSON.")
        return value


class StrictAdmin(admin.ModelAdmin):
    """No staff permission escalation through Django admin models."""

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


class VNPayRuleInline(admin.TabularInline):
    model = VNPayRule
    extra = 1
    fields = ("position", "code", "label", "category", "expression", "explanation")

    def has_add_permission(self, request, obj):
        return bool(request.user.is_superuser and (obj is None or obj.status == "draft"))

    def has_change_permission(self, request, obj=None):
        return bool(request.user.is_superuser and (obj is None or obj.status == "draft"))

    def has_delete_permission(self, request, obj=None):
        return bool(request.user.is_superuser and (obj is None or obj.status == "draft"))


@admin.register(VNRuleSet)
class VNRuleSetAdmin(StrictAdmin):
    list_display = ("code", "title", "company", "version", "status", "effective_from", "effective_to", "preview_link")
    list_filter = ("status", "company")
    search_fields = ("code", "title")
    readonly_fields = ("created_by", "approved_by", "approved_at", "created_at", "status")
    inlines = [VNPayRuleInline]
    actions = ["submit_for_review", "return_to_draft", "approve_checked", "retire_approved"]

    def get_inlines(self, request, obj):
        if obj is not None and obj.status != "draft":
            return []
        return super().get_inlines(request, obj)

    def get_readonly_fields(self, request, obj=None):
        if obj and obj.status != "draft":
            return [field.name for field in obj._meta.fields]
        return super().get_readonly_fields(request, obj)

    def has_delete_permission(self, request, obj=None):
        return super().has_delete_permission(request, obj) and (obj is None or obj.status == "draft")

    def save_model(self, request, obj, form, change):
        if not change:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)

    def preview_link(self, obj):
        return format_html('<a href="{}/preview/">Tính thử</a>', obj.pk)
    preview_link.short_description = "Thử công thức"

    @admin.action(description="Chuyển bộ Nháp sang Chờ duyệt")
    def submit_for_review(self, request, queryset):
        for item in queryset:
            if item.status != "draft" or not item.lines.exists():
                self.message_user(request, f"Bỏ qua {item}: phải có dòng công thức và đang Nháp.", level=messages.WARNING)
                continue
            item.status = "review"
            try:
                item.save()
                self.message_user(request, f"Đã gửi duyệt: {item}", level=messages.SUCCESS)
            except ValidationError as exc:
                self.message_user(request, str(exc), level=messages.ERROR)

    @admin.action(description="Trả lại trạng thái Nháp để sửa công thức")
    def return_to_draft(self, request, queryset):
        for item in queryset:
            if item.status != "review":
                continue
            item.status = "draft"
            item.approved_by = None
            item.approved_at = None
            item.save()
            self.message_user(request, f"Đã trả lại bản nháp {item}.", level=messages.SUCCESS)

    @admin.action(description="Phê duyệt bộ công thức (khác người tạo)")
    def approve_checked(self, request, queryset):
        for item in queryset:
            try:
                with transaction.atomic():
                    locked = VNRuleSet._base_manager.select_for_update().get(pk=item.pk)
                    locked.approve(request.user)
                self.message_user(request, f"Đã duyệt: {locked}", level=messages.SUCCESS)
            except ValidationError as exc:
                self.message_user(request, f"Không thể duyệt {item}: {exc}", level=messages.ERROR)

    @admin.action(description="Ngừng áp dụng bộ đã duyệt")
    def retire_approved(self, request, queryset):
        for item in queryset:
            if item.status != "approved":
                self.message_user(request, f"Không thể ngừng bộ chưa duyệt: {item}", level=messages.ERROR)
                continue
            item.status = "retired"
            item.save()
            self.message_user(request, f"Đã ngừng áp dụng: {item}", level=messages.SUCCESS)

    def get_urls(self):
        own = [
            path("<int:object_id>/preview/", self.admin_site.admin_view(self.preview_view), name="vn_payroll_ruleset_preview")
        ]
        return own + super().get_urls()

    def preview_view(self, request, object_id):
        if not request.user.is_active or not request.user.is_superuser:
            return HttpResponseForbidden("Bạn không có quyền xem chức năng tính thử.")
        rule_set = get_object_or_404(VNRuleSet, pk=object_id)
        form = RulePreviewForm(request.POST or None)
        result, error = None, None
        if request.method == "POST" and form.is_valid():
            try:
                result = preview_ruleset(rule_set, form.cleaned_data["inputs"])
            except ValidationError as exc:
                error = "; ".join(exc.messages)
        return render(
            request,
            "admin/vn_payroll/preview.html",
            {"title": "Tính thử công thức (không ghi bảng lương)", "form": form,
             "rule_set": rule_set, "result": result, "error": error,
             **self.admin_site.each_context(request)},
        )

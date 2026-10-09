from django import forms
from django.contrib import admin

from .models import AdminLog


class AdminLogForm(forms.ModelForm):
    details = forms.CharField(
        widget=forms.Textarea,
        help_text="Manual entries are clearly labeled and do not replace automatic audit events.",
    )

    class Meta:
        model = AdminLog
        fields = ("details",)

    def clean_details(self):
        details = self.cleaned_data["details"].strip()
        if not details:
            raise forms.ValidationError("Enter a note for the admin log.")
        return details


@admin.register(AdminLog)
class AdminLogAdmin(admin.ModelAdmin):
    form = AdminLogForm
    list_display = ("admin_user", "action", "target_type", "target_id", "created_at")
    list_filter = ("action", "target_type", "created_at")
    date_hierarchy = "created_at"
    search_fields = (
        "action",
        "details",
        "target_type",
        "target_id",
        "admin_user__username",
    )
    list_select_related = ("admin_user",)
    list_per_page = 50
    readonly_fields = (
        "admin_user",
        "action",
        "details",
        "target_type",
        "target_id",
        "changes",
        "created_at",
    )

    def get_fields(self, request, obj=None):
        if obj is None:
            return ("details",)
        return self.readonly_fields

    def get_readonly_fields(self, request, obj=None):
        if obj is None:
            return ()
        return self.readonly_fields

    def save_model(self, request, obj, form, change):
        if not change:
            obj.admin_user = request.user
            obj.action = "manual_note"
            obj.target_type = "admin_note"
            obj.target_id = ""
            obj.changes = {}
        super().save_model(request, obj, form, change)

    def has_delete_permission(self, request, obj=None):
        return False

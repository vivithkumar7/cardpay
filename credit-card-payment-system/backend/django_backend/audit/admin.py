from django.contrib import admin
from .models import AdminLog

@admin.register(AdminLog)
class AdminLogAdmin(admin.ModelAdmin):
    list_display = ("admin_user", "action", "created_at")
    search_fields = ("action", "details", "admin_user__username")
    readonly_fields = ("created_at",)

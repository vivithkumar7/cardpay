from django.contrib import admin
from django.contrib.auth import get_user_model
from django.contrib.auth.admin import UserAdmin
from .models import UserCreditProfile

User = get_user_model()
admin.site.unregister(User)
admin.site.register(User, UserAdmin)


@admin.register(UserCreditProfile)
class UserCreditProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "credit_limit")
    search_fields = ("user__username", "user__email")

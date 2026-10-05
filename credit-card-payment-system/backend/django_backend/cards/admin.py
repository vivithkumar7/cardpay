from django.contrib import admin
from .models import Card

@admin.register(Card)
class CardAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "card_type", "masked_card_number", "last4", "created_at")
    search_fields = ("user__username", "last4", "card_holder_name")
    readonly_fields = ("masked_card_number", "last4", "created_at")

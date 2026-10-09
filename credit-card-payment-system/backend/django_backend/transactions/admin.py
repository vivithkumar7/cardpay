import json

from django import forms
from django.contrib import admin
from django.db import transaction as db_transaction
from django.utils.html import format_html_join

from audit.models import AdminLog
from .models import FraudAlert, Transaction


class FraudAlertAdminForm(forms.ModelForm):
    rule_codes = forms.JSONField(
        help_text='Enter one or more rule codes as a JSON list, for example ["manual_review"].'
    )

    class Meta:
        model = FraudAlert
        fields = ("transaction", "rule_codes")

    def clean_rule_codes(self):
        rule_codes = self.cleaned_data["rule_codes"]
        if not isinstance(rule_codes, list) or not rule_codes:
            raise forms.ValidationError("Enter at least one fraud rule code.")
        if any(not isinstance(code, str) or not code.strip() for code in rule_codes):
            raise forms.ValidationError(
                "Fraud rule codes must be non-empty strings."
            )
        return [code.strip() for code in rule_codes]


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = (
        "reference",
        "user",
        "amount",
        "currency",
        "status",
        "fraud_status",
        "created_at",
    )
    list_filter = ("status", "fraud_status", "currency", "created_at")
    search_fields = ("reference", "user__username")
    readonly_fields = ("reference", "created_at", "updated_at", "audit_history")

    @admin.display(description="Admin audit history")
    def audit_history(self, obj):
        if obj is None or obj.pk is None:
            return "Save the transaction before viewing its audit history."

        logs = AdminLog.objects.filter(
            target_type="transaction",
            target_id=str(obj.pk),
        ).select_related("admin_user")
        return format_html_join(
            "",
            "<p><strong>{}</strong> by {} at {}<br>{}<br>{}</p>",
            (
                (
                    log.action,
                    log.admin_user.get_username() if log.admin_user else "Deleted user",
                    log.created_at,
                    log.details,
                    json.dumps(log.changes, sort_keys=True),
                )
                for log in logs
            ),
        ) or "No admin actions have been recorded for this transaction."

    def save_model(self, request, obj, form, change):
        original = None
        if change:
            original = self.get_queryset(request).get(pk=obj.pk)

        super().save_model(request, obj, form, change)

        changes = {}
        if original is not None:
            for field in obj._meta.concrete_fields:
                if getattr(field, "auto_now", False) or getattr(
                    field, "auto_now_add", False
                ):
                    continue
                before = getattr(original, field.attname)
                after = getattr(obj, field.attname)
                if before != after:
                    changes[field.name] = {
                        "before": str(before),
                        "after": str(after),
                    }

        if not change or changes:
            action = "transaction_updated" if change else "transaction_created"
            AdminLog.objects.create(
                admin_user=request.user,
                action=action,
                details=(
                    f"Transaction {obj.reference} was "
                    f"{'updated' if change else 'created'} in Django Admin."
                ),
                target_type="transaction",
                target_id=str(obj.pk),
                changes=changes,
            )


@admin.register(FraudAlert)
class FraudAlertAdmin(admin.ModelAdmin):
    form = FraudAlertAdminForm
    list_display = (
        "transaction",
        "user",
        "review_status",
        "detected_at",
        "reviewed_by",
    )
    list_filter = ("review_status", "detected_at")
    search_fields = ("transaction__reference", "user__username", "rule_codes")
    autocomplete_fields = ("transaction",)
    readonly_fields = (
        "transaction",
        "user",
        "rule_codes",
        "review_status",
        "detected_at",
        "reviewed_by",
        "reviewed_at",
    )

    def get_fields(self, request, obj=None):
        if obj is None:
            return ("transaction", "rule_codes")
        return self.readonly_fields

    def get_readonly_fields(self, request, obj=None):
        if obj is None:
            return ()
        return self.readonly_fields

    @db_transaction.atomic
    def save_model(self, request, obj, form, change):
        if not change:
            payment = obj.transaction
            previous_fraud_status = payment.fraud_status
            payment.fraud_status = Transaction.FraudStatus.FLAGGED
            payment.save(update_fields=["fraud_status"])
            obj.user = payment.user

        super().save_model(request, obj, form, change)

        if not change:
            AdminLog.objects.create(
                admin_user=request.user,
                action="fraud_alert_manually_created",
                details=(
                    f"Fraud alert for transaction {payment.reference} "
                    "was manually created in Django Admin."
                ),
                target_type="fraud_alert",
                target_id=str(obj.pk),
                changes={
                    "fraud_status": {
                        "before": previous_fraud_status,
                        "after": Transaction.FraudStatus.FLAGGED,
                    },
                    "rule_codes": {"before": [], "after": obj.rule_codes},
                },
            )

    def has_delete_permission(self, request, obj=None):
        return False

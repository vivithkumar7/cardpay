from rest_framework.permissions import BasePermission, SAFE_METHODS


def _has_permission(user, permission):
    return user.is_staff or user.has_perm(permission)


def can_initiate_payments(user):
    if _has_permission(user, "cards.manage_cards"):
        return True
    has_operations_role = user.has_perm(
        "cards.view_all_cards"
    ) or user.has_perm("transactions.view_all_transactions")
    return not has_operations_role


class CanViewAllCards(BasePermission):
    def has_permission(self, request, view):
        return _has_permission(request.user, "cards.view_all_cards")


class CanManageCards(BasePermission):
    def has_permission(self, request, view):
        user = request.user
        if request.method in SAFE_METHODS:
            return _has_permission(user, "cards.view_all_cards")
        if request.method == "PATCH":
            if _has_permission(user, "cards.manage_cards"):
                return True
            return (
                user.has_perm("cards.block_cards")
                and set(request.data) == {"is_active"}
            )
        if request.method == "DELETE":
            return _has_permission(user, "cards.manage_cards")
        return False


class CanManagePersonalCards(BasePermission):
    def has_permission(self, request, view):
        return request.method in SAFE_METHODS or can_initiate_payments(
            request.user
        )


class CanViewAllTransactions(BasePermission):
    def has_permission(self, request, view):
        return _has_permission(request.user, "transactions.view_all_transactions")


class CanViewAnalytics(BasePermission):
    def has_permission(self, request, view):
        return _has_permission(request.user, "transactions.view_analytics")


class CanReviewFraudAlerts(BasePermission):
    def has_permission(self, request, view):
        return _has_permission(request.user, "transactions.review_fraud_alerts")

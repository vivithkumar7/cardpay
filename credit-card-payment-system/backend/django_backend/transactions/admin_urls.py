from django.urls import path
from .views import (
    AdminSummaryView,
    FraudAlertListView,
    FraudAlertReviewView,
    AnalyticsExportView,
    SystemHealthView,
    TransactionExportView,
)
from cards.admin_views import (
    AdminCardActivityView,
    AdminCardDetailView,
    AdminCardListView,
)

urlpatterns = [
    path("export/", TransactionExportView.as_view()),
    path("summary/", AdminSummaryView.as_view()),
    path("system-health/", SystemHealthView.as_view()),
    path("analytics/export/", AnalyticsExportView.as_view()),
    path("fraud-alerts/", FraudAlertListView.as_view()),
    path("fraud-alerts/<int:pk>/", FraudAlertReviewView.as_view()),
    path("cards/", AdminCardListView.as_view()),
    path("cards/<int:pk>/activity/", AdminCardActivityView.as_view()),
    path("cards/<int:pk>/", AdminCardDetailView.as_view()),
]

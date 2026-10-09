from django.urls import path
from .views import CardUsageAnalyticsView, TransactionListView
from .statements import MonthlyStatementPdfView

urlpatterns = [
    path("", TransactionListView.as_view()),
    path("analytics/usage/", CardUsageAnalyticsView.as_view()),
    path("statement/", MonthlyStatementPdfView.as_view()),
]

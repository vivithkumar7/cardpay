from django.urls import path
from .views import TransactionListView
from .statements import MonthlyStatementPdfView

urlpatterns = [
    path("", TransactionListView.as_view()),
    path("statement/", MonthlyStatementPdfView.as_view()),
]

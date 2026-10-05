from django.urls import path
from .views import TransactionExportView, AdminSummaryView

urlpatterns = [
    path("export/", TransactionExportView.as_view()),
    path("summary/", AdminSummaryView.as_view()),
]

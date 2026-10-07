from django.urls import path
from .views import (
    InternalDashboardSummaryView,
    InternalTransactionCreateView,
    InternalTransactionUpdateView,
)

urlpatterns = [
    path("dashboard/summary/", InternalDashboardSummaryView.as_view()),
    path("create/", InternalTransactionCreateView.as_view()),
    path("<str:reference>/", InternalTransactionUpdateView.as_view()),
]

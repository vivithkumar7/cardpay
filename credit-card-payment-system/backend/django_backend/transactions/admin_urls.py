from django.urls import path
from .views import TransactionExportView, AdminSummaryView
from cards.admin_views import (
    AdminCardActivityView,
    AdminCardDetailView,
    AdminCardListView,
)

urlpatterns = [
    path("export/", TransactionExportView.as_view()),
    path("summary/", AdminSummaryView.as_view()),
    path("cards/", AdminCardListView.as_view()),
    path("cards/<int:pk>/activity/", AdminCardActivityView.as_view()),
    path("cards/<int:pk>/", AdminCardDetailView.as_view()),
]

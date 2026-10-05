from django.urls import path
from .views import InternalTransactionCreateView, InternalTransactionUpdateView

urlpatterns = [
    path("create/", InternalTransactionCreateView.as_view()),
    path("<str:reference>/", InternalTransactionUpdateView.as_view()),
]

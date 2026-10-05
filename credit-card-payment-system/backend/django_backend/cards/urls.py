from django.urls import path
from .views import CardListCreateView, CardDeleteView

urlpatterns = [
    path("", CardListCreateView.as_view()),
    path("<int:pk>/", CardDeleteView.as_view()),
]

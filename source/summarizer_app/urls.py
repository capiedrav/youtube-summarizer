from django.urls import path
from .views import UrlView

urlpatterns = [
    path("", UrlView.as_view(), name="summarizer"),
]


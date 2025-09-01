from django.urls import path
from .views import UrlView, VideoSummaryView, VideoSummaryListView

urlpatterns = [
    path("video-summaries/<str:pk>", VideoSummaryView.as_view(), name="video-summary"),
    path("video-summaries/", VideoSummaryListView.as_view(), name="video-summary-list"),
    path("", UrlView.as_view(), name="home"),
  
]

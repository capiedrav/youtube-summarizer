from django.urls import path
from .views import UrlView, VideoSummaryView

urlpatterns = [
    path("video-summary/<str:pk>", VideoSummaryView.as_view(), name="video_summary"),
    path("", UrlView.as_view(), name="home"),
  
]

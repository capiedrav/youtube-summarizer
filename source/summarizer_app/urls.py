from django.urls import path
from .views import UrlView, VideoSummaryView, VideoSummaryListView, CheckStatusView, CeleryErrorView

urlpatterns = [
    path("video-summaries/<str:pk>", VideoSummaryView.as_view(), name="video-summary"),
    path("video-summaries/check-status/<str:task_id>", CheckStatusView.as_view(), name="check-status"),
    path("video-summaries/", VideoSummaryListView.as_view(), name="video-summary-list"),
    path("server-error/", CeleryErrorView.as_view(), name="celery-error" ),
    path("", UrlView.as_view(), name="home"),
  
]

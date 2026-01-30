from celery import shared_task
from celery.result import AsyncResult
from .models import YTSummary
from .youtube import get_video_id


@shared_task
def create_summary(youtube_url: str) -> None:
    """
    Celery task to create summary from YouTube URL.
    """

    YTSummary.summaries.create(youtube_url=youtube_url)

def trigger_create_summary(youtube_url: str) -> AsyncResult:
    """
    Triggers create_summary task.
    """

    video_id = get_video_id(youtube_url)

    return create_summary.apply_async(args=[youtube_url, ], task_id=video_id) # task_id is video_id

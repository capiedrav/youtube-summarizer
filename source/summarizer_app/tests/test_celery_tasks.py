from celery.result import AsyncResult
from django.test import TestCase, override_settings
from summarizer_app.tasks import create_summary, trigger_create_summary
from unittest.mock import patch
from summarizer_app.models import YTSummary


class CeleryTasksTests(TestCase):

    def setUp(self) -> None:

        self.youtube_url = "https://www.youtube.com/watch?v=5bId3N7QZec"

        self.yt_summary = YTSummary(
            video_id="5bId3N7QZec",
            url=self.youtube_url,
            video_text="bla bla",
            video_summary="""
            {
                "overview": "video overview",
                "key_takeaways": [
                    "takeaway_1",
                    "takeaway_2",
                    "takeaway_3",
                    "takeaway_4"
                ],
                "conclusion": "conclusion"
            }
            """
        )

        self.yt_summary.save()

    @override_settings(CELERY_TASK_EAGER_PROPAGATES=True) # raise errors in celery worker
    @override_settings(CELERY_TASK_ALWAYS_EAGER=True) # run celery task locally
    @patch("summarizer_app.tasks.YTSummary.summaries.create")
    def test_create_summary(self, mocked_create):

        mocked_create.return_value = self.yt_summary
        video_id = "5bId3N7QZec"

        # apply_async runs synchronously
        result = create_summary.apply_async(args=[self.youtube_url, ], task_id=video_id)

        self.assertEqual(result.status, "SUCCESS")
        self.assertEqual(result.task_id, video_id) # check task_id is video_id
        mocked_create.assert_called_once_with(youtube_url=self.youtube_url)

    @patch("summarizer_app.tasks.create_summary.apply_async")
    def test_trigger_create_summary(self, mocked_apply_async):

        video_id = "5bId3N7QZec"
        mocked_apply_async.return_value = AsyncResult(id=video_id)

        result = trigger_create_summary(self.youtube_url)

        self.assertEqual(result.task_id, video_id) # check task_id is video_id
        mocked_apply_async.assert_called_once_with(args=[self.youtube_url, ], task_id=video_id)

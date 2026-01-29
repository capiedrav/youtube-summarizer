from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import transaction
from django.test import TestCase
from summarizer_app.models import YTSummary
from unittest.mock import patch


class YTSummaryModelTests(TestCase):
    """
    Tests for YTSummary model.
    """

    def setUp(self):

        self.youtube_url = "https://www.youtube.com/watch?v=5bId3N7QZec"
        self.video_id = "5bId3N7QZec"
        
        # load video text
        with open(settings.BASE_DIR / "summarizer_app/tests/test_video_text.txt", "r") as video_text:
            self.video_text = video_text.read()

        # load video summary
        with open(settings.BASE_DIR / "summarizer_app/tests/test_video_summary.txt", "r") as text_summary:
            self.video_summary = text_summary.read()

    @patch("summarizer_app.models.get_video_summary")
    def test_can_create_YTSummary(self, mocked_get_video_summary):

        mocked_get_video_summary.return_value = (
            self.video_id,
            self.video_summary,
            self.video_text,
            "video title",
            f"thumbnails/{self.video_id}.jpg"
        )

        YTSummary.summaries.create(youtube_url=self.youtube_url)

        self.assertEqual(YTSummary.summaries.count(), 1)
        mocked_get_video_summary.assert_called_once_with(self.youtube_url)
        # check thumbnails are saved at expected location
        expected_path = (settings.THUMBNAILS_PATH / f"{self.video_id}.jpg").resolve().as_posix() # normalize path
        self.assertEqual(expected_path, YTSummary.summaries.first().thumbnail.path)

    def test_create_YTSummary_with_default_title_and_thumbnail(self):

        yt_summary = YTSummary(
            # note that title and thumbnail fields are not defined
            video_id=self.video_id,
            url=self.youtube_url,
            video_text=self.video_text,
            video_summary=self.video_summary
        )

        yt_summary.save()

        self.assertEqual(YTSummary.summaries.count(), 1)

        # check default title was saved
        yt_summary = YTSummary.summaries.first()
        self.assertEqual(yt_summary.title, "Title Not Available")

        # check default thumbnail was saved
        expected_path = (settings.THUMBNAILS_PATH / "thumbnail_not_found.jpg").resolve() # normalize path
        self.assertEqual(expected_path.as_posix(), yt_summary.thumbnail.path)

    def test_cant_create_YTSummary_with_wrong_url(self):

        yt_summary = YTSummary(
            video_id=self.video_id,
            url="www.google.com", # wrong url
            title="video title",
            thumbnail="thumbnails/thumbnail.jpg",
            video_text=self.video_text,
            video_summary=self.video_summary
        )

        with self.assertRaises(ValidationError):
            yt_summary.save()
        self.assertEqual(YTSummary.summaries.count(), 0)

    def test_cant_save_YTSummary_instance_with_incomplete_fields(self):
        # note that title and thumbnail fields are not defined because they have default values

        with self.assertRaises(ValidationError):
            with transaction.atomic(): # for the reason to use this check: https://stackoverflow.com/questions/21458387/transactionmanagementerror-you-cant-execute-queries-until-the-end-of-the-atom
                yt_summary = YTSummary(  # no video id
                    # video_id=self.video_id,
                    url=self.youtube_url,
                    title="video title",
                    thumbnail="thumbnails/thumbnail.jpg",
                    video_text=self.video_text,
                    video_summary=self.video_summary
                )
                yt_summary.save()

        with self.assertRaises(ValidationError):
            with transaction.atomic():
                yt_summary = YTSummary( # no url
                    video_id=self.video_id,
                    # url=self.youtube_url,
                    title="video title",
                    thumbnail="thumbnails/thumbnail.jpg",
                    video_text=self.video_text,
                    video_summary=self.video_summary
                )
                yt_summary.save()

        with self.assertRaises(ValidationError):
            with transaction.atomic():
                yt_summary = YTSummary( # no video_text
                    video_id=self.video_id,
                    url=self.youtube_url,
                    title="video title",
                    thumbnail="thumbnails/thumbnail.jpg",
                    # video_text=self.video_text,
                    video_summary=self.video_summary
                )
                yt_summary.save()

        with self.assertRaises(ValidationError):
            with transaction.atomic():
                yt_summary = YTSummary( # no video_summary
                    video_id=self.video_id,
                    url=self.youtube_url,
                    title="video title",
                    thumbnail="thumbnails/thumbnail.jpg",
                    video_text=self.video_text,
                    # video_summary=self.video_summary
                )
                yt_summary.save()
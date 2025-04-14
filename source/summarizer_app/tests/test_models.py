from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.test import TestCase
from summarizer_app.models import YTSummary


class YTSummaryModelTests(TestCase):
    """
    Tests for YTSummary model.
    """

    def setUp(self):

        self.youtube_urls = [
            "https://www.youtube.com/watch?v=5bId3N7QZec",
            "https://www.youtube.com/watch?v=y20xJyl46dE",
            "https://www.youtube.com/watch?v=CU5Riqb4PBg",
        ]

        self.video_ids = [
            "5bId3N7QZec",
            "y20xJyl46dE",
            "CU5Riqb4PBg",
        ]

        # load video text
        with open(settings.BASE_DIR / "summarizer_app/test_video_text.txt", "r") as video_text:
            self.video_text = video_text.read()

        # load video summary
        with open(settings.BASE_DIR / "summarizer_app/test_video_summary.txt", "r") as text_summary:
            self.video_summary = text_summary.read()

    def test_can_create_YTSummary(self):

        YTSummary.objects.create(
            video_id=self.video_ids[0],
            url=self.youtube_urls[0],
            video_text=self.video_text,
            video_summary=self.video_summary)

        self.assertEqual(YTSummary.objects.count(), 1)

    def test_cant_create_YTSummary_with_wrong_url(self):

        yt_summary = YTSummary(
            video_id=self.video_ids[0],
            url="www.google.com", # wrong url
            video_text=self.video_text,
            video_summary=self.video_summary
        )

        with self.assertRaises(ValidationError):
            yt_summary.full_clean()
            yt_summary.save()
        self.assertEqual(YTSummary.objects.count(), 0)

    def test_cant_save_YTSummary_instance_with_incomplete_fields(self):

        with self.assertRaises(IntegrityError):
            with transaction.atomic(): # for the reason to use this check: https://stackoverflow.com/questions/21458387/transactionmanagementerror-you-cant-execute-queries-until-the-end-of-the-atom
                YTSummary.objects.create( # no video_id
                    url=self.youtube_urls[0],
                    video_text=self.video_text,
                    video_summary=self.video_summary
                )

        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                YTSummary.objects.create( # no url
                    video_id=self.video_ids[0],
                    video_text=self.video_text,
                    video_summary=self.video_summary
                )

        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                YTSummary.objects.create( # no video_text
                    video_id=self.video_ids[0],
                    url=self.youtube_urls[0],
                    video_summary=self.video_summary
                )

        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                YTSummary.objects.create( # no video_summary
                    video_id=self.video_ids[0],
                    url=self.youtube_urls[0],
                    video_text=self.video_text,
                )

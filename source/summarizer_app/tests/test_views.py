from unittest.mock import patch, MagicMock
from django.conf import settings
from django.test import TestCase, Client
from django.urls import resolve, reverse
from summarizer_app.forms import YoutubeUrlForm
from summarizer_app.models import YTSummary
from summarizer_app.views import UrlView, VideoSummaryView, VideoSummaryListView
from .test_forms import custom_recaptcha_response
from youtube_transcript_api import RequestBlocked
import json


class UrlViewTests(TestCase):
    """
    Tests for the UrlView class.
    """

    def setUp(self):

        self.client = Client()
        self.payload = {"url": "https://www.youtube.com/watch?v=EXWJZ2jEe6I", "captcha": "PASSED"}

    @staticmethod
    def config_mocks(mocked_get_video_id, mocked_get_video_summary, mocked_submit):

        video_id = "EXWJZ2jEe6I"
        video_title = "Base 5x91 | ¿Será juzgado Milei por la cryptoestafa piramidal LIBRA?"
        video_thumbnail = f"thumbnails/{video_id}"

        with open(settings.BASE_DIR / "summarizer_app/tests/test_video_summary.txt", "r") as test_video_summary:
            video_summary = test_video_summary.read()
        with open(settings.BASE_DIR / "summarizer_app/tests/test_video_text.txt", "r") as test_video_text:
            video_text = test_video_text.read()

        mocked_get_video_id.return_value = video_id
        mocked_get_video_summary.return_value = (
            video_id,
            video_summary,
            video_text,
            video_title,
            video_thumbnail
        )
        mocked_submit.return_value = custom_recaptcha_response(score=0.9)

    def test_home_url_resolves_to_UrlView(self):

        view = resolve(reverse("home"))

        self.assertEqual(view.func.view_class, UrlView)

    def test_UrlView_renders_the_right_template(self):

        response = self.client.get(reverse("home"))

        self.assertTemplateUsed(response, "summarizer_app/home.html")

    def test_UrlView_uses_the_right_form(self):

        response = self.client.get(reverse("home"))

        self.assertIsInstance(response.context["form"], YoutubeUrlForm)
        # self.assertContains(response, response.context["form"])


    @patch("django_recaptcha.fields.client.submit")
    @patch("summarizer_app.models.get_video_summary")
    @patch("summarizer_app.views.get_video_id")
    def test_post_to_UrlView_redirects_to_VideoSummaryView(self, mocked_get_video_id, mocked_get_video_summary,
                                                           mocked_submit):

        self.config_mocks(mocked_get_video_id, mocked_get_video_summary, mocked_submit)

        response = self.client.post(path=reverse("home"), data=self.payload, follow=True)

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "summarizer_app/video_summary.html")
        mocked_get_video_id.assert_called_once_with(self.payload["url"])
        mocked_get_video_summary.assert_called_once_with(self.payload["url"])
        mocked_submit.assert_called_once()

    @patch("django_recaptcha.fields.client.submit")
    @patch("summarizer_app.models.get_video_summary")
    @patch("summarizer_app.views.get_video_id")
    def test_post_to_UrlView_saves_video_summary(self, mocked_get_video_id, mocked_get_video_summary, mocked_submit):

        self.config_mocks(mocked_get_video_id, mocked_get_video_summary, mocked_submit)

        response = self.client.post(reverse("home"), data=self.payload)

        self.assertEqual(response.status_code, 302)
        yt_summary = YTSummary.summaries.get(pk=mocked_get_video_id.return_value)

        self.assertEqual(YTSummary.summaries.count(), 1)
        self.assertEqual(yt_summary.video_id, mocked_get_video_summary.return_value[0])
        self.assertEqual(yt_summary.url, self.payload["url"])
        self.assertEqual(yt_summary.video_summary, mocked_get_video_summary.return_value[1])
        self.assertEqual(yt_summary.video_text, mocked_get_video_summary.return_value[2])
        self.assertEqual(yt_summary.title, mocked_get_video_summary.return_value[3])
        self.assertEqual(yt_summary.thumbnail, mocked_get_video_summary.return_value[4])
        mocked_get_video_id.assert_called_once_with(self.payload["url"])
        mocked_get_video_summary.assert_called_once_with(self.payload["url"])
        mocked_submit.assert_called_once()

    @patch("django_recaptcha.fields.client.submit")
    def test_post_to_UrlView_with_wrong_url_doesnt_render_video_summary(self, mocked_submit):

        mocked_submit.return_value = custom_recaptcha_response(score=0.9)

        response = self.client.post(reverse("home"), data={"url": "www.google.com", "captcha": "PASSED"})

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "summarizer_app/home.html")
        self.assertEqual(YTSummary.summaries.count(), 0)
        mocked_submit.assert_called_once()

    @patch("django_recaptcha.fields.client.submit")
    def test_post_to_UrlView_with_wrong_url_doesnt_saves_video_summary(self, mocked_submit):

        mocked_submit.return_value = custom_recaptcha_response(score=0.9)

        response = self.client.post(reverse("home"), data={"url": "www.google.com", "captcha": "PASSED"})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(YTSummary.summaries.count(), 0)
        mocked_submit.assert_called_once()

    @patch("django_recaptcha.fields.client.submit")
    def test_post_to_UrlView_with_invalid_captcha_doesnt_render_video_summary(self, mocked_submit):

        mocked_submit.return_value = custom_recaptcha_response(score=0.2) # invalid captcha

        response = self.client.post(reverse("home"), data=self.payload)

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "summarizer_app/home.html")
        self.assertEqual(YTSummary.summaries.count(), 0)
        mocked_submit.assert_called_once()

    @patch("django_recaptcha.fields.client.submit")
    def test_post_to_UrlView_with_invalid_captcha_doesnt_saves_video_summary(self, mocked_submit):

        mocked_submit.return_value = custom_recaptcha_response(score=0.2) # invalid captcha

        response = self.client.post(reverse("home"), data=self.payload)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(YTSummary.summaries.count(), 0)
        mocked_submit.assert_called_once()

    @patch("django_recaptcha.fields.client.submit")
    @patch("summarizer_app.models.get_video_summary")
    @patch("summarizer_app.views.get_video_id")
    def test_post_to_UrlView_with_existing_yt_summary_doesnt_call_get_video_summary(self,
                                                                                    mocked_get_video_id,
                                                                                    mocked_get_video_summary,
                                                                                    mocked_submit
                                                                                    ):

        # create a video summary
        YTSummary(
            video_id="EXWJZ2jEe6I",
            url=self.payload["url"],
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
        ).save()

        self.config_mocks(mocked_get_video_id, mocked_get_video_summary, mocked_submit)

        # make a POST request for the same video
        response = self.client.post(reverse("home"), data=self.payload, follow=True)

        self.assertEqual(response.status_code, 200)
        mocked_get_video_id.assert_called_once_with(self.payload["url"])
        self.assertEqual(mocked_get_video_summary.call_count, 0) # get_video_summary was not called
        self.assertEqual(YTSummary.summaries.count(), 1)
        mocked_submit.assert_called_once()

    @patch("django_recaptcha.fields.client.submit")
    @patch("summarizer_app.models.get_video_summary")
    @patch("summarizer_app.views.get_video_id")
    def test_post_to_UrlView_logs_exceptions(self, mocked_get_video_id, mocked_get_video_summary, mocked_submit):
        """
        Checks any exception is logged.
        """

        video_id = "EXWJZ2jEe6I"
        mocked_get_video_id.return_value = video_id
        mocked_get_video_summary.side_effect = Exception("Something went wrong")
        mocked_submit.return_value = custom_recaptcha_response(score=0.9)

        # check the logger logs an error
        with self.assertLogs(logger="summarizer_app.views", level="ERROR"):
            with self.assertRaises(Exception):
                self.client.post(reverse("home"), data=self.payload)

        mocked_submit.assert_called_once()
        mocked_get_video_summary.assert_called_once_with(self.payload["url"])
        mocked_get_video_id.assert_called_once_with(self.payload["url"])

    @patch("django_recaptcha.fields.client.submit")
    @patch("summarizer_app.models.get_video_summary")
    @patch("summarizer_app.views.get_video_id")
    def test_post_to_UrlView_logs_specific_exception(self, mocked_get_video_id, mocked_get_video_summary,
                                                     mocked_submit):
        """
        Check that specific exceptions are logged, e.g., RequestBlocked exception.
        """

        video_id = "EXWJZ2jEe6I"
        mocked_get_video_id.return_value = video_id
        mocked_get_video_summary.side_effect = RequestBlocked(video_id)
        mocked_submit.return_value = custom_recaptcha_response(score=0.9)

        # check logger logs an RequestBlocked error
        with self.assertLogs(logger="summarizer_app.views", level="ERROR"):
            with self.assertRaises(RequestBlocked):
                self.client.post(reverse("home"), data=self.payload)

        mocked_submit.assert_called_once()
        mocked_get_video_summary.assert_called_once_with(self.payload["url"])
        mocked_get_video_id.assert_called_once_with(self.payload["url"])

    @patch("django_recaptcha.fields.client.submit")
    @patch("summarizer_app.models.get_video_summary")
    @patch("summarizer_app.views.get_video_id")
    def test_exceptions_in_UrlView_render_custom_server_error_page(self, mocked_get_video_id, mocked_get_video_summary,
                                                                   mocked_submit):
        video_id = "EXWJZ2jEe6I"
        mocked_get_video_id.return_value = video_id
        mocked_get_video_summary.side_effect = Exception("Something went wrong")
        mocked_submit.return_value = custom_recaptcha_response(score=0.9)

        self.client.raise_request_exception = False # do not capture the exception to be raised in the POST request
        response = self.client.post(reverse("home"), data=self.payload)

        self.assertEqual(response.status_code, 500)
        self.assertTemplateUsed(response, "500.html")
        mocked_get_video_summary.assert_called_once_with(self.payload["url"])
        mocked_get_video_id.assert_called_once_with(self.payload["url"])

    def test_wrong_url_path_renders_custom_404_error_page(self):

        response = self.client.get("/wrong-url/")

        self.assertEqual(response.status_code, 404)
        self.assertTemplateUsed(response, "404.html")


class VideoSummaryViewTests(TestCase):
    """
    Tests for the VideoSummaryView class.
    """

    def setUp(self):

        self.client = Client()
        YTSummary(
            video_id="EXWJZ2jEe6I",
            url="https://www.youtube.com/watch?v=EXWJZ2jEe6I",
            title="test title",
            thumbnail="thumbnails/EXWJZ2jEe6I.jpg",
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
            """).save()

    def test_video_summary_url_resolves_to_VideoSummaryView(self):

        view = resolve(reverse("video-summary", kwargs={"pk": "EXWJZ2jEe6I"}))

        self.assertEqual(view.func.view_class, VideoSummaryView)

    def test_VideoSummaryView_renders_video_summary_video_text(self):

        response = self.client.get(reverse("video-summary", kwargs={"pk": "EXWJZ2jEe6I"}))

        yt_summary = YTSummary.summaries.get(pk="EXWJZ2jEe6I")
        video_summary = response.context["video_summary"]

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "summarizer_app/video_summary.html")
        self.assertContains(response, yt_summary.title)
        self.assertContains(response, yt_summary.thumbnail)
        self.assertContains(response, video_summary["overview"][:20])
        self.assertContains(response, video_summary["key_takeaways"][0][:20])
        self.assertContains(response, video_summary["conclusion"][:20])
        self.assertContains(response, yt_summary.video_text[:20])


class VideoSummaryListViewTests(TestCase):
    """
    Tests for the VideoSummariesListView class.
    """

    def setUp(self):

        self.client = Client()
        summaries = []
        for i in range(1, 11): # create 10 database entries
            summaries.append(YTSummary(
                video_id=f"video_{i}",
                url=f"https://www.youtube.com/watch?v=video_{i}",
                title=f"video {i}",
                thumbnail=f"thumbnails/thumbnail_{i}.jpg",
                video_text=f"transcript video {i}",
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
            )
        YTSummary.summaries.bulk_create(summaries) # save database entries with a single query

    def test_video_summaries_url_resolves_to_VideoSummariesListView(self):

        view = resolve(reverse("video-summary-list"))

        self.assertEqual(view.func.view_class, VideoSummaryListView)

    def test_VideoSummaryListView_renders_video_summary_list(self):

        response = self.client.get(reverse("video-summary-list"))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "summarizer_app/video_summaries.html")
        self.assertEqual(YTSummary.summaries.count(), 10)

        # get the first and last video summaries in the database
        yt_1 = YTSummary.summaries.get(pk="video_1")
        yt_10 = YTSummary.summaries.get(pk="video_10")

        # check they're rendered in the template
        self.assertContains(response, yt_1.title)
        self.assertContains(response, yt_1.thumbnail.url)
        self.assertContains(response, json.loads(yt_1.video_summary)["overview"])
        self.assertContains(response, yt_10.title)
        self.assertContains(response, yt_10.thumbnail.url)
        self.assertContains(response, json.loads(yt_10.video_summary)["overview"])

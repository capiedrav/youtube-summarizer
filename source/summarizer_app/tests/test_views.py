from unittest.mock import patch
from django.conf import settings
from django.test import TestCase, Client
from django.urls import resolve, reverse
from summarizer_app.forms import YoutubeUrlForm
from summarizer_app.models import YTSummary
from summarizer_app.utils import EmptyTranscriptError, RequestBlocked
from summarizer_app.views import UrlView, VideoSummaryView
from .test_forms import custom_recaptcha_response


class UrlViewTests(TestCase):
    """
    Tests for the UrlView class.
    """

    def setUp(self):

        self.client = Client()
        self.payload = {"url": "https://www.youtube.com/watch?v=EXWJZ2jEe6I", "captcha": "PASSED"}

    @staticmethod
    def config_mocks(mock_get_video_id, mock_get_video_summary, mocked_submit):
        mock_get_video_id.return_value = "EXWJZ2jEe6I"
        with open(settings.BASE_DIR / "summarizer_app/tests/test_video_summary.txt", "r") as test_video_summary:
            with open(settings.BASE_DIR / "summarizer_app/tests/test_video_text.txt", "r") as test_video_text:
                mock_get_video_summary.return_value = (test_video_summary.read(), test_video_text.read())

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
    @patch("summarizer_app.views.get_video_summary")
    @patch("summarizer_app.views.get_video_id")
    def test_post_to_UrlView_redirects_to_VideoSummaryView(self, mock_get_video_id, mock_get_video_summary,
                                                           mocked_submit):

        self.config_mocks(mock_get_video_id, mock_get_video_summary, mocked_submit)

        response = self.client.post(path=reverse("home"), data=self.payload, follow=True)

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "summarizer_app/video_summary.html")
        mock_get_video_id.assert_called_once()
        mock_get_video_summary.assert_called_once()
        mocked_submit.assert_called_once()

    @patch("django_recaptcha.fields.client.submit")
    @patch("summarizer_app.views.get_video_summary")
    @patch("summarizer_app.views.get_video_id")
    def test_post_to_UrlView_saves_video_summary(self, mock_get_video_id, mock_get_video_summary, mocked_submit):

        self.config_mocks(mock_get_video_id, mock_get_video_summary, mocked_submit)

        response = self.client.post(reverse("home"), data=self.payload)

        self.assertEqual(response.status_code, 302)
        yt_summary = YTSummary.objects.get(pk=mock_get_video_id.return_value)

        self.assertEqual(YTSummary.objects.count(), 1)
        self.assertEqual(yt_summary.video_id, mock_get_video_id.return_value)
        self.assertEqual(yt_summary.url, self.payload["url"])
        self.assertEqual(yt_summary.video_summary, mock_get_video_summary.return_value[0])
        self.assertEqual(yt_summary.video_text, mock_get_video_summary.return_value[1])
        mock_get_video_id.assert_called_once()
        mock_get_video_summary.assert_called_once()
        mocked_submit.assert_called_once()

    @patch("django_recaptcha.fields.client.submit")
    def test_post_to_UrlView_with_wrong_url_doesnt_render_video_summary(self, mocked_submit):

        mocked_submit.return_value = custom_recaptcha_response(score=0.9)

        response = self.client.post(reverse("home"), data={"url": "www.google.com", "captcha": "PASSED"})

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "summarizer_app/home.html")
        self.assertEqual(YTSummary.objects.count(), 0)
        mocked_submit.assert_called_once()

    @patch("django_recaptcha.fields.client.submit")
    def test_post_to_UrlView_with_wrong_url_doesnt_saves_video_summary(self, mocked_submit):

        mocked_submit.return_value = custom_recaptcha_response(score=0.9)

        response = self.client.post(reverse("home"), data={"url": "www.google.com", "captcha": "PASSED"})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(YTSummary.objects.count(), 0)
        mocked_submit.assert_called_once()

    @patch("django_recaptcha.fields.client.submit")
    def test_post_to_UrlView_with_invalid_captcha_doesnt_render_video_summary(self, mocked_submit):

        mocked_submit.return_value = custom_recaptcha_response(score=0.2) # invalid captcha

        response = self.client.post(reverse("home"), data=self.payload)

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "summarizer_app/home.html")
        self.assertEqual(YTSummary.objects.count(), 0)
        mocked_submit.assert_called_once()

    @patch("django_recaptcha.fields.client.submit")
    def test_post_to_UrlView_with_invalid_captcha_doesnt_saves_video_summary(self, mocked_submit):

        mocked_submit.return_value = custom_recaptcha_response(score=0.2) # invalid captcha

        response = self.client.post(reverse("home"), data=self.payload)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(YTSummary.objects.count(), 0)
        mocked_submit.assert_called_once()

    @patch("django_recaptcha.fields.client.submit")
    @patch("summarizer_app.views.get_video_summary")
    @patch("summarizer_app.views.get_video_id")
    def test_post_to_UrlView_with_existing_yt_summary_doesnt_call_get_video_summary(self,
                                                                                    mock_get_video_id,
                                                                                    mock_get_video_summary,
                                                                                    mocked_submit
                                                                                    ):

        # create a video summary
        YTSummary.objects.create(
            video_id="EXWJZ2jEe6I",
            url=self.payload["url"],
            video_text="bla bla",
            video_summary="bla bla"
        )

        self.config_mocks(mock_get_video_id, mock_get_video_summary, mocked_submit)

        # make a POST request for the same video
        response = self.client.post(reverse("home"), data=self.payload)

        self.assertEqual(response.status_code, 302)
        mock_get_video_id.assert_called_once()
        self.assertEqual(mock_get_video_summary.call_count, 0) # get_video_summary was not called
        self.assertEqual(YTSummary.objects.count(), 1)
        mocked_submit.assert_called_once()

    @patch("django_recaptcha.fields.client.submit")
    @patch("summarizer_app.views.get_video_summary")
    @patch("summarizer_app.views.get_video_id")
    def test_post_to_UrlView_logs_EmptyTranscriptError(self, mock_get_video_id, mock_get_video_summary, mocked_submit):

        video_id = "EXWJZ2jEe6I"
        mock_get_video_id.return_value = video_id
        mock_get_video_summary.side_effect = EmptyTranscriptError(video_id)
        mocked_submit.return_value = custom_recaptcha_response(score=0.9)

        # check the logger logs an error
        with self.assertLogs(logger="summarizer_app.views", level="ERROR"):
            with self.assertRaises(EmptyTranscriptError):
                self.client.post(reverse("home"), data=self.payload)

        mocked_submit.assert_called_once()

    @patch("django_recaptcha.fields.client.submit")
    @patch("summarizer_app.views.get_video_summary")
    @patch("summarizer_app.views.get_video_id")
    def test_post_to_UrlView_logs_RequestBlocked_exception(self, mock_get_video_id, mock_get_video_summary,
                                                           mocked_submit):

        video_id = "EXWJZ2jEe6I"
        mock_get_video_id.return_value = video_id
        mock_get_video_summary.side_effect = RequestBlocked(video_id)
        mocked_submit.return_value = custom_recaptcha_response(score=0.9)

        # check the logger logs and error
        with self.assertLogs(logger="summarizer_app.views", level="ERROR"):
            with self.assertRaises(RequestBlocked):
                self.client.post(reverse("home"), data=self.payload)

        mocked_submit.assert_called_once()

    @patch("django_recaptcha.fields.client.submit")
    @patch("summarizer_app.views.get_video_summary")
    @patch("summarizer_app.views.get_video_id")
    def test_exceptions_in_UrlView_renders_custom_server_error_page(self, mock_get_video_id, mock_get_video_summary,
                                                                        mocked_submit):
        video_id = "EXWJZ2jEe6I"
        mock_get_video_id.return_value = video_id
        mock_get_video_summary.side_effect = RequestBlocked(video_id)
        mocked_submit.return_value = custom_recaptcha_response(score=0.9)

        self.client.raise_request_exception = False # do not capture the exception to be raised in the POST request
        response = self.client.post(reverse("home"), data=self.payload)

        self.assertEqual(response.status_code, 500)
        self.assertTemplateUsed(response, "500.html")

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
        YTSummary.objects.create(video_id="EXWJZ2jEe6I", url="https://www.youtube.com/watch?v=EXWJZ2jEe6I",
                                 video_text="bla bla", video_summary="ble ble")

    def test_video_summary_url_resolves_to_VideoSummaryView(self):

        view = resolve(reverse("video_summary", kwargs={"pk": "EXWJZ2jEe6I"}))

        self.assertEqual(view.func.view_class, VideoSummaryView)

    def test_VideoSummaryView_renders_video_summary_video_text(self):

        response = self.client.get(reverse("video_summary", kwargs={"pk": "EXWJZ2jEe6I"}))

        yt_summary = YTSummary.objects.get(pk="EXWJZ2jEe6I")

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "summarizer_app/video_summary.html")
        self.assertContains(response, yt_summary.video_summary[:20])
        self.assertContains(response, yt_summary.video_text[:20])

from unittest.mock import patch

from django.conf import settings
from django.test import TestCase, Client
from django.urls import resolve, reverse

from summarizer_app.forms import YoutubeUrlForm
from summarizer_app.models import YTSummary
from summarizer_app.views import UrlView


class UrlViewTests(TestCase):

    def setUp(self):

        self.client = Client()
        self.payload = {"url": "https://www.youtube.com/watch?v=EXWJZ2jEe6I"}

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

    @patch("summarizer_app.views.get_video_summary")
    @patch("summarizer_app.views.get_video_id")
    def test_can_post_to_UrlView(self, mock_get_video_id, mock_get_video_summary):

        mock_get_video_id.return_value = "EXWJZ2jEe6I"
        with open(settings.BASE_DIR / "summarizer_app/test_video_summary.txt", "r") as test_video_summary:
            mock_get_video_summary.return_value = test_video_summary.read()

        response = self.client.post(reverse("home"), data=self.payload, follow=False)

        self.assertEqual(response.status_code, 200)
        mock_get_video_id.assert_called_once()
        mock_get_video_summary.assert_called_once()

    @patch("summarizer_app.views.get_video_summary")
    @patch("summarizer_app.views.get_video_id")
    def test_post_to_UrlView_renders_video_summary(self,  mock_get_video_id, mock_get_video_summary):

        mock_get_video_id.return_value = "EXWJZ2jEe6I"
        with open(settings.BASE_DIR / "summarizer_app/test_video_summary.txt", "r") as test_video_summary:
            video_summary = test_video_summary.read()
            mock_get_video_summary.return_value = video_summary

        response = self.client.post(reverse("home"), data=self.payload)

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "summarizer_app/home.html")
        self.assertContains(response, video_summary[:20])

    @patch("summarizer_app.views.get_video_summary")
    @patch("summarizer_app.views.get_video_id")
    def test_post_to_UrlView_saves_video_summary(self, mock_get_video_id, mock_get_video_summary):

        mock_get_video_id.return_value = "EXWJZ2jEe6I"
        with open(settings.BASE_DIR / "summarizer_app/test_video_summary.txt", "r") as test_video_summary:
            mock_get_video_summary.return_value = test_video_summary.read()

        response = self.client.post(reverse("home"), data=self.payload)

        self.assertEqual(response.status_code, 200)
        yt_summary = YTSummary.objects.get(pk=mock_get_video_id.return_value)

        self.assertEqual(YTSummary.objects.count(), 1)
        self.assertEqual(yt_summary.video_id, mock_get_video_id.return_value)
        self.assertEqual(yt_summary.url, self.payload["url"])
        self.assertEqual(yt_summary.video_text, "bla bla")
        self.assertEqual(yt_summary.video_summary, mock_get_video_summary.return_value)

    def test_post_to_UrlView_with_wrong_url_doesnt_render_video_summary(self):

        response = self.client.post(reverse("home"), data={"url": "www.google.com"})

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "summarizer_app/home.html")
        self.assertIsNone(response.context.get("video_summary"))
        self.assertEqual(YTSummary.objects.count(), 0)

    def test_post_to_UrlView_with_wrong_url_doesnt_saves_video_summary(self):

        response = self.client.post(reverse("home"), data={"url": "www.google.com"})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(YTSummary.objects.count(), 0)

    @patch("summarizer_app.views.get_video_summary")
    @patch("summarizer_app.views.get_video_id")
    def test_post_to_UrlView_with_existing_yt_summary_doesnt_call_get_video_summary(self, mock_get_video_id, mock_get_video_summary):

        # create a video summary
        YTSummary.objects.create(
            video_id="EXWJZ2jEe6I",
            url=self.payload["url"],
            video_text="bla bla",
            video_summary="bla bla"
        )

        mock_get_video_id.return_value = "EXWJZ2jEe6I"

        # make a POST request for the same video
        response = self.client.post(reverse("home"), data=self.payload)

        self.assertEqual(response.status_code, 200)
        mock_get_video_id.assert_called_once()
        self.assertEqual(mock_get_video_summary.call_count, 0) # get_video_summary was not called
        self.assertEqual(YTSummary.objects.count(), 1)

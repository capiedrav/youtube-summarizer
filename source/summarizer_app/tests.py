from django.test import TestCase
from .views import UrlView
from django.test import SimpleTestCase, Client
from django.urls import reverse, resolve
from .utils import get_video_id, get_video_text, WrongUrlError, get_text_summary, get_video_summary, \
                   get_proxy_server
from .forms import YoutubeUrlForm
from unittest.mock import patch
from youtube_transcript_api._errors import TranscriptsDisabled
from fp.fp import FreeProxyException
from random import choice
from django.conf import settings
from unittest import skip, skipIf
from django.core.exceptions import ValidationError
import os


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

    @skipIf(os.environ.get("GITHUB_ACTIONS") is not None, reason="This test fails in github actions")
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

    def test_post_to_UrlView_with_wrong_url_doesnt_render_video_summary(self):

        response = self.client.post(reverse("home"), data={"url": "www.google.com"})
        
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "summarizer_app/home.html")
        self.assertIsNone(response.context.get("video_summary"))


class YoutubeURLFormTests(TestCase):
    """
    Tests for Youtube url form.
    """

    def test_form_validates_youtube_url(self):

        test_url = "https://www.youtube.com/watch?v=5bId3N7QZec"
        form = YoutubeUrlForm(data={"url": test_url})
        
        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data["url"], test_url)

    def test_form_not_valid_on_wrong_url(self):

        form = YoutubeUrlForm(data={"url": "https://www.google.com"})
        
        self.assertFalse(form.is_valid()) 
        self.assertEqual(form.cleaned_data.get("url"), None)        


class UtilsTests(TestCase):
    """
    Tests for utility tools.
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

        self.proxy_servers = [
            "http://3.141.217.225:80",
            "http://71.14.218.2:8080",
            "http://71.14.218.2:8080",
            "http://52.196.1.182:80",
            "http://18.228.149.161:80"
        ]

    def test_extract_videoId_from_youtube_url(self):

        for i in range(len(self.youtube_urls)):
            self.assertEqual(self.video_ids[i], get_video_id(self.youtube_urls[i]))

    def test_trying_to_extract_videoId_from_wrong_url_raises_wrong_url_error(self):

        # note that the url doesn't have the 'v=' separator
        wrong_url = "https://www.youtube.com/watch?5bId3N7QZec" 

        with self.assertRaises(WrongUrlError):
            get_video_id(wrong_url) 

        # note that the url has two 'v=' separators
        wrong_url = "https://www.youtube.com/watch?v=5bId3N7QZec?v=5bId3N7QZec?" 

        with self.assertRaises(WrongUrlError):
            get_video_id(wrong_url) 

    def test_get_proxy_server(self):

        # get the ip address of a randomly selected proxy server
        proxy = get_proxy_server()         

        self.assertIsInstance(proxy, str)
        self.assertIn("http://", proxy)

    @patch("summarizer_app.utils.FreeProxy")
    def test_get_proxy_server_raises_error_after_three_failures(self, mock_FreeProxy):
        
        # mock proxy_server object inside get_proxy_server function
        proxy_server = mock_FreeProxy.return_value
        # get method raises FreeProxyException
        proxy_server.get.side_effect = FreeProxyException(message="There are no working proxies at this time.")

        # check the exception was raised
        with self.assertRaises(FreeProxyException):
            get_proxy_server()

        # check the get method was called three times
        self.assertEqual(proxy_server.get.call_count, 3)

    @skipIf(os.environ.get("GITHUB_ACTIONS") is not None, reason="This test fails in github actions")
    @patch("summarizer_app.utils.get_proxy_server")
    def test_get_video_text(self, mock_get_proxy_server):
                
        # mock get_proxy_server function       
        mock_get_proxy_server.return_value = choice(self.proxy_servers)
        
        # call the function under text with a random video id                
        video_text = get_video_text(choice(self.video_ids))
        
        # check that the function was called
        mock_get_proxy_server.assert_called_once()        

        # check video text is a string
        self.assertIsInstance(video_text, str)

    @patch("summarizer_app.utils.YTA")
    @patch("summarizer_app.utils.get_proxy_server")
    def test_get_video_text_raises_error_after_three_failures(self, mock_get_proxy_server, mock_YTA):

        # mock get_proxy_server function       
        mock_get_proxy_server.return_value = choice(self.proxy_servers)
        
        video_id = choice(self.video_ids)
        
        # get_transcript method raises TranscriptsDisabled exception
        mock_YTA.get_transcript.side_effect = TranscriptsDisabled(video_id)

        # check the exception was raised
        with self.assertRaises(TranscriptsDisabled):
            get_video_text(video_id)

        # check the get_transcript method was called three times
        self.assertEqual(mock_YTA.get_transcript.call_count, 3)

    @skipIf(
        os.environ.get("TEST_DEEPSEEK_API") is None,
        reason="This test is time and money consuming, because it calls the deepseek api"
     )    
    def test_get_text_summary(self):
        
        with open(settings.BASE_DIR / "summarizer_app/test_video_text.txt", "r") as video_text:
            text = video_text.read()
        
        text_summary = get_text_summary(text)
        
        print(text_summary)
        self.assertIsInstance(text_summary, str)

    @patch("summarizer_app.utils.get_text_summary")
    @patch("summarizer_app.utils.get_video_text")
    def test_get_video_summary(self, mock_get_video_text, mock_get_text_summary):

        video_id = self.video_ids[0]

        # mock get_video_text function
        with open(settings.BASE_DIR / "summarizer_app/test_video_text.txt", "r") as video_text:
            mock_get_video_text.return_value = video_text.read()        
                 
        # mock get_text_summary function
        with open(settings.BASE_DIR / "summarizer_app/test_video_summary.txt", "r") as text_summary:
            mock_get_text_summary.return_value = text_summary.read()

        # call the function under test
        video_summary = get_video_summary(video_id)
        
        # verify that the mocked functions were called
        mock_get_video_text.assert_called_once()
        mock_get_text_summary.assert_called_once()

        self.assertIsInstance(video_summary, str)
        
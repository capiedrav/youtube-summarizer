from django.test import TestCase
from .views import UrlView
from django.test import SimpleTestCase, Client
from django.urls import reverse, resolve
from .utils import get_video_id, get_video_text, WrongUrlError, get_text_summary, get_video_summary
from unittest.mock import patch
import fp.fp # free-proxy module
from random import choice
from django.conf import settings
from unittest import skip


class UrlViewTests(TestCase):

    def setUp(self):

        self.client = Client()

    def test_summarizer_url_resolves_to_URLView(self):

        view = resolve(reverse("summarizer"))

        self.assertEqual(view.func.view_class, UrlView)

    def test_can_post_to_UrlView(self):
        
        payload = {"youtubeUrl": "https://www.youtube.com/watch?v=EXWJZ2jEe6I"}
        response = self.client.post(reverse("summarizer"), data=payload, follow=False)

        self.assertEqual(response.status_code, 302)


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

    def test_free_proxy(self):

        # get the ip address of a randomly selected proxy server
        proxy = fp.fp.FreeProxy(rand=True).get()         

        self.assertIsInstance(proxy, str)

    @patch("summarizer_app.utils.FreeProxy")
    def test_get_video_text(self, mock_FreeProxy):

        # mock proxy_server object inside get_video_text function
        proxy_server = mock_FreeProxy.return_value
        proxy_server.get.return_value = choice(self.proxy_servers) # select a proxy server randomly

        # call the function under text with a random video id                
        video_text = get_video_text(choice(self.video_ids))
        
        # check that the get method of the mocked object was called
        proxy_server.get.assert_called_once()        

        # check video text is a string
        self.assertIsInstance(video_text, str)        

    @skip(reason="This test is time and money consuming, because it calls the deepseek api")    
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
        
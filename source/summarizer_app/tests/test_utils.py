import os
from random import choice
from unittest import skipIf
from unittest.mock import patch
from django.conf import settings
from django.test import TestCase
from fp.errors import FreeProxyException
from youtube_transcript_api import TranscriptsDisabled
from summarizer_app.utils import get_video_id, WrongUrlError, get_proxy_server, get_video_text, get_text_summary, \
    get_video_summary


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
        video_summary, video_text = get_video_summary(video_id)

        # verify that the mocked functions were called
        mock_get_video_text.assert_called_once()
        mock_get_text_summary.assert_called_once()

        self.assertIsInstance(video_summary, str)
        self.assertIsInstance(video_text, str)

import os
from random import choice
from unittest import skipIf
from unittest.mock import patch
from django.conf import settings
from django.test import TestCase
from youtube_transcript_api import RequestBlocked, FetchedTranscript, FetchedTranscriptSnippet
from youtube_transcript_api import YouTubeTranscriptApi as YTA
from youtube_transcript_api.proxies import WebshareProxyConfig
from summarizer_app.utils import get_video_id, WrongUrlError, get_video_text, get_text_summary, \
    get_video_summary, EmptyTranscriptError
from xml.etree.ElementTree import ParseError
from xml.parsers.expat import ExpatError


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

    @skipIf(
        condition=os.environ.get("TEST_YOUTUBE_TRANSCRIPT_API") is None,
        reason="This test is time and money consuming, because it uses a paid proxy"
    )
    def test_youtube_transcript_api(self):

        ytt_api = YTA(
            proxy_config=WebshareProxyConfig(
                proxy_username=os.environ.get("PROXY_USERNAME"),
                proxy_password=os.environ.get("PROXY_PASSWORD")
            )
        )

        transcript = ytt_api.fetch(video_id=self.video_ids[0])

        self.assertIsInstance(transcript, FetchedTranscript)

    @patch("summarizer_app.utils.YTA.fetch")
    def test_get_video_text(self, mock_fetch):

        mock_fetch.return_value = FetchedTranscript(
            snippets=[
                FetchedTranscriptSnippet(text="Test line 1", start=0.0, duration=1.50),
                FetchedTranscriptSnippet(text="line between", start=1.5, duration=2.0),
                FetchedTranscriptSnippet(
                    text="testing the end line", start=2.5, duration=3.25
                ),
            ],
            language="English",
            language_code="en",
            is_generated=True,
            video_id="12345",
        )

        # call the function under text with a random video id
        video_text = get_video_text(choice(self.video_ids))

        mock_fetch.assert_called_once() # check that the mocked function was called
        self.assertEqual(video_text, "Test line 1\nline between\ntesting the end line")

    @patch("summarizer_app.utils.YTA.fetch")
    def test_get_video_text_raises_RequestBlocked_exception_after_three_failures(self, mock_fetch):

        video_id = choice(self.video_ids)

        # fetch method raises RequestBlocked exception
        mock_fetch.side_effect = RequestBlocked(video_id)

        # check the exception was raised
        with self.assertRaises(RequestBlocked):
            get_video_text(video_id)

        # check the get_transcript method was called three times
        self.assertEqual(mock_fetch.call_count, 3)

    @patch("summarizer_app.utils.YTA.fetch")
    def test_get_video_text_ExpatError_or_ParseError_raises_EmptyTranscriptError(self, mock_fetch):
        """
        This issue is discussed in:
        https://github.com/jdepoix/youtube-transcript-api/issues/414
        https://github.com/jdepoix/youtube-transcript-api/issues/320
        """

        video_id = choice(self.video_ids)

        # fetch method raises Expat exception
        mock_fetch.side_effect = ExpatError()

        # check get_video_text raises EmptyTranscriptError
        with self.assertRaises(EmptyTranscriptError):
            get_video_text(video_id)

        # get_transcript method raises ParseError exception
        mock_fetch.side_effect = ParseError()

        # check get_video_text raises EmptyTranscriptError
        with self.assertRaises(EmptyTranscriptError):
            get_video_text(video_id)

        # check fetch method is call two times, one for ExpatError and the other for ParseError
        self.assertEqual(mock_fetch.call_count, 2)

    @skipIf(
        condition=os.environ.get("TEST_DEEPSEEK_API") is None,
        reason="This test is time and money consuming, because it calls the deepseek api"
     )
    def test_get_text_summary(self):

        with open(settings.BASE_DIR / "summarizer_app/tests/test_video_text.txt", "r") as video_text:
            text = video_text.read()

        text_summary = get_text_summary(text)

        self.assertIsInstance(text_summary, str)

    @patch("summarizer_app.utils.get_text_summary")
    @patch("summarizer_app.utils.get_video_text")
    def test_get_video_summary(self, mock_get_video_text, mock_get_text_summary):

        video_id = self.video_ids[0]

        # mock get_video_text function
        with open(settings.BASE_DIR / "summarizer_app/tests/test_video_text.txt", "r") as video_text:
            mock_get_video_text.return_value = video_text.read()

        # mock get_text_summary function
        with open(settings.BASE_DIR / "summarizer_app/tests/test_video_summary.txt", "r") as text_summary:
            mock_get_text_summary.return_value = text_summary.read()

        # call the function under test
        video_summary, video_text = get_video_summary(video_id)

        # verify that the mocked functions were called
        mock_get_video_text.assert_called_once()
        mock_get_text_summary.assert_called_once()

        self.assertIsInstance(video_summary, str)
        self.assertIsInstance(video_text, str)

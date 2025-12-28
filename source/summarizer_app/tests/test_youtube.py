import shutil
from tempfile import NamedTemporaryFile
import requests
from django.test import TestCase
from unittest import skipIf
from unittest.mock import patch, PropertyMock
from django.conf import settings
from pytubefix import YouTube
from requests import Response
from summarizer_app.youtube import get_video_id, WrongUrlError, get_video_text, get_video_title, _get_thumbnail_url, \
    _get_thumbnail_image, _save_thumbnail_image, get_video_thumbnail
from youtube_transcript_api import YouTubeTranscriptApi as YTA
from youtube_transcript_api import FetchedTranscript, FetchedTranscriptSnippet, RequestBlocked
from youtube_transcript_api.proxies import WebshareProxyConfig
from random import choice
import os
import io


class YoutubeTests(TestCase):
    """
    Tests for YouTube related functions.
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

    @patch("summarizer_app.youtube.YTA.fetch")
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

        mock_fetch.assert_called_once()  # check that the mocked function was called
        self.assertEqual(video_text, "Test line 1\nline between\ntesting the end line")

    @patch("summarizer_app.youtube.YTA.fetch")
    def test_get_video_text_raises_RequestBlocked_exception_after_three_failures(self, mock_fetch):
        """
        RequestBlocked is a typical exception from youtube-transcript-api.
        """

        video_id = choice(self.video_ids)

        # fetch method raises RequestBlocked exception
        mock_fetch.side_effect = RequestBlocked(video_id)

        # check the exception was raised
        with self.assertRaises(RequestBlocked):
            get_video_text(video_id)

        # check fetch method was called three times
        self.assertEqual(mock_fetch.call_count, 3)

    @patch("summarizer_app.youtube.YTA.fetch")
    def test_get_video_text_raises_exception_after_three_failures(self, mock_fetch):
        """
        Test for other kinds of exceptions that could happen, e.g., proxy-related exceptions.
        """

        video_id = choice(self.video_ids)

        # fetch method raises an exception
        mock_fetch.side_effect = Exception("Something went wrong")

        with self.assertRaises(Exception):
            get_video_text(video_id)

        # check fetch method was called three times
        self.assertEqual(mock_fetch.call_count, 3)

    @patch("summarizer_app.youtube.YouTube.title", new_callable=PropertyMock)
    def test_get_video_title(self, mocked_title):

        mocked_title.return_value = "Youtube Video Title"

        title = get_video_title(youtube_url=self.youtube_urls[0])

        self.assertEqual(title, mocked_title.return_value)
        mocked_title.assert_called_once()

    @patch("summarizer_app.youtube.YouTube.title", new_callable=PropertyMock)
    def test_get_video_title_raises_exception_after_three_failures(self, mocked_title):

        mocked_title.side_effect = Exception("Something went wrong")

        with self.assertRaises(Exception):
            get_video_title(youtube_url=self.youtube_urls[0])

        self.assertEqual(mocked_title.call_count, 3)

    @patch("summarizer_app.youtube.YouTube.thumbnail_url", new_callable=PropertyMock)
    def test_get_thumbnail_url(self, mocked_thumbnail_url):

        mocked_thumbnail_url.return_value = "www.youtube-video-thumbnail.com"

        thumbnail_url = _get_thumbnail_url(youtube_url=self.youtube_urls[0])

        self.assertEqual(thumbnail_url, mocked_thumbnail_url.return_value)
        mocked_thumbnail_url.assert_called_once()

    @patch("summarizer_app.youtube.YouTube.thumbnail_url", new_callable=PropertyMock)
    def test_get_thumbnail_url_raises_exception_after_three_failures(self, mocked_thumbnail_url):

        mocked_thumbnail_url.side_effect = Exception("Something went wrong")

        with self.assertRaises(Exception):
            _get_thumbnail_url(youtube_url=self.youtube_urls[0])
        self.assertEqual(mocked_thumbnail_url.call_count, 3)

    @patch("summarizer_app.youtube.requests.get")
    def test_get_thumbnail_image(self, mocked_get):

        mocked_get.return_value = Response()
        mocked_get.return_value.raw = io.BytesIO(b"thumbnail data")

        self.assertEqual(_get_thumbnail_image(self.youtube_urls[0]).raw, mocked_get.return_value.raw)

    @patch("summarizer_app.youtube.requests.get")
    def test_get_thumbnail_image_raises_exception_after_three_failures(self, mocked_get):

        mocked_get.side_effect = Exception("Something went wrong")

        with self.assertRaises(Exception):
            _get_thumbnail_image(self.youtube_urls[0])
        self.assertEqual(mocked_get.call_count, 3)

    @patch("summarizer_app.youtube.shutil.copyfileobj")
    @patch("summarizer_app.youtube.open")
    def test_save_video_thumbnail(self, mocked_open, mocked_copyfileobj):

        response = Response()
        response.raw = io.BytesIO(b"thumbnail data")

        thumbnail_path = (settings.THUMBNAILS_PATH / f"{self.video_ids[0]}.jpg").resolve().as_posix()

        thumbnail_rel_path = _save_thumbnail_image(response, self.video_ids[0])
        expected_path = f"thumbnails/{self.video_ids[0]}.jpg"

        self.assertEqual(thumbnail_rel_path, expected_path)
        mocked_open.assert_called_once_with(thumbnail_path, "wb")
        mocked_copyfileobj.assert_called_once()

    @patch("summarizer_app.youtube._get_thumbnail_url")
    @patch("summarizer_app.youtube._get_thumbnail_image")
    @patch("summarizer_app.youtube._save_thumbnail_image")
    def test_get_video_thumbnail(self, mocked_save_thumbnail_image, mocked_get_thumbnail_image, mocked_get_thumbnail_url):

        mocked_get_thumbnail_url.return_value = "www.youtube-video-thumbnail.com"
        mocked_get_thumbnail_image.return_value = Response()
        mocked_get_thumbnail_image.return_value.raw = io.BytesIO(b"thumbnail data")
        mocked_get_thumbnail_image.return_value.status_code = 200
        mocked_save_thumbnail_image.return_value = f"thumbnails/{self.video_ids[0]}.jpg"

        thumbnail_rel_path = get_video_thumbnail(self.youtube_urls[0])

        expected_path = f"thumbnails/{self.video_ids[0]}.jpg"
        self.assertEqual(thumbnail_rel_path, expected_path)

        mocked_get_thumbnail_url.assert_called_once()
        mocked_get_thumbnail_image.assert_called_once()
        mocked_save_thumbnail_image.assert_called_once()

    @patch("summarizer_app.youtube._get_thumbnail_url")
    @patch("summarizer_app.youtube._get_thumbnail_image")
    @patch("summarizer_app.youtube._save_thumbnail_image")
    def test_cant_get_video_thumbnail_on_wrong_response(self, mocked_save_thumbnail_image, mocked_get_thumbnail_image,
                                                        mocked_get_thumbnail_url):

        mocked_get_thumbnail_url.return_value = "www.youtube-video-thumbnail.com"
        mocked_get_thumbnail_image.return_value = Response()
        mocked_get_thumbnail_image.return_value.raw = io.BytesIO(b"") # no thumbnail data
        mocked_get_thumbnail_image.return_value.status_code = 404 # wrong status code


        thumbnail_rel_path = get_video_thumbnail(self.youtube_urls[0])

        self.assertIsNone(thumbnail_rel_path) # no thumbnail path
        mocked_get_thumbnail_url.assert_called_once()
        mocked_get_thumbnail_image.assert_called_once()
        mocked_save_thumbnail_image.assert_not_called() # _save_thumbnail_image is not called


@skipIf(
    condition=os.getenv("TEST_PYTUBEFIX_API") is None,
    reason="These tests are time and money consuming, because they use a paid proxy."
)
class PytubeFixTests(TestCase):
    """
    Tests for pytubefix module.
    """

    def setUp(self):

        self.youtube_url = "https://www.youtube.com/watch?v=5bId3N7QZec"

        # concat '-rotate' to PROXY_USERNAME for automatic proxy ip address rotation
        proxy_username = os.getenv("PROXY_USERNAME") + "-rotate"
        proxy_password = os.getenv("PROXY_PASSWORD")

        # config proxies
        self.proxies = {
            "http": f"http://{proxy_username}:{proxy_password}@p.webshare.io:80",
            "https": f"http://{proxy_username}:{proxy_password}@p.webshare.io:80",
        }

    def test_get_video_title(self):

        yt = YouTube(url=self.youtube_url, proxies=self.proxies)

        self.assertEqual(yt.title, "how programmers overprepare for job interviews")

    def test_get_video_thumbnail(self):

        yt = YouTube(url=self.youtube_url, proxies=self.proxies)

        req = requests.get(yt.thumbnail_url, proxies=self.proxies, stream=True)

        with NamedTemporaryFile(mode="wb", suffix=".jpg") as thumbnail:
            req.raw.decode_content = True
            shutil.copyfileobj(req.raw, thumbnail)

            self.assertIn(".jpg", thumbnail.name)
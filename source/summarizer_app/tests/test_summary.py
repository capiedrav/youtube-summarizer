from django.test import TestCase
from unittest import skipIf
from unittest.mock import patch
from django.conf import settings
from summarizer_app.summary import get_text_summary, get_video_summary
import json
import os


class SummaryTests(TestCase):

    @skipIf(
        condition=os.environ.get("TEST_DEEPSEEK_API") is None,
        reason="This test is time and money consuming, because it calls the deepseek api"
    )
    def test_get_text_summary(self):

        # types of the values of the dict
        expected_value_types = {"overview": str, "key_takeaways": list, "conclusion": str}

        with open(settings.BASE_DIR / "summarizer_app/tests/test_video_text.txt", "r") as video_text:
            text = video_text.read()

        text_summary = get_text_summary(text)  # summary as json string
        summary_dict = json.loads(text_summary)  # summary as dict

        # check the dict has the correct number of key-value pairs
        keys = list(summary_dict.keys())
        self.assertEqual(len(keys), len(expected_value_types))

        # check the dict has the correct key names
        for key in expected_value_types:
            self.assertIn(key, keys)

        # check the dict values have the correct type
        for key in expected_value_types:
            self.assertIsInstance(summary_dict[key], expected_value_types[key])

    @patch("summarizer_app.summary.get_video_thumbnail")
    @patch("summarizer_app.summary.get_video_title")
    @patch("summarizer_app.summary.get_text_summary")
    @patch("summarizer_app.summary.get_video_text")
    @patch("summarizer_app.summary.get_video_id")
    def test_get_video_summary(self, mocked_get_video_id, mock_get_video_text, mock_get_text_summary,
                               mocked_get_video_title, mocked_get_video_thumbnail):
        youtube_url = "https://www.youtube.com/watch?v=5bId3N7QZec"
        video_id = "5bId3N7QZec"

        mocked_get_video_id.return_value = video_id

        # mock get_video_text function
        with open(settings.BASE_DIR / "summarizer_app/tests/test_video_text.txt", "r") as video_text:
            mock_get_video_text.return_value = video_text.read()

        # mock get_text_summary function
        with open(settings.BASE_DIR / "summarizer_app/tests/test_video_summary.txt", "r") as text_summary:
            mock_get_text_summary.return_value = text_summary.read()

        mocked_get_video_title.return_value = "video title"
        mocked_get_video_thumbnail.return_value = "thumbnail path"

        # call the function under test
        video_id, video_summary, video_text, video_title, video_thumbnail = get_video_summary(youtube_url)

        # verify that the mocked functions were called
        mocked_get_video_id.assert_called_once_with(youtube_url)
        mock_get_video_text.assert_called_once_with(video_id)
        mock_get_text_summary.assert_called_once_with(mock_get_video_text.return_value)
        mocked_get_video_title.assert_called_once_with(youtube_url)
        mocked_get_video_thumbnail.assert_called_once_with(youtube_url)

        # verify the get_video_summary returns the correct information
        self.assertEqual(video_summary, mock_get_text_summary.return_value)
        self.assertEqual(video_text, mock_get_video_text.return_value)
        self.assertEqual(video_title, mocked_get_video_title.return_value)
        self.assertEqual(video_thumbnail, mocked_get_video_thumbnail.return_value)
from django.test import TestCase
from summarizer_app.forms import YoutubeUrlForm
from unittest.mock import patch
from django_recaptcha.client import RecaptchaResponse


class YoutubeURLFormTests(TestCase):
    """
    Tests for Youtube url form.
    """

    @patch("django_recaptcha.fields.client.submit")
    def test_form_validates_youtube_url(self, mocked_submit):

        mocked_submit.return_value = RecaptchaResponse(
            is_valid=True,
            extra_data={"score": 0.9},
            action="youtube_url_form"
        )

        test_url = "https://www.youtube.com/watch?v=5bId3N7QZec"
        form = YoutubeUrlForm(data={"url": test_url, "captcha": "PASSED"})
        
        self.assertTrue(form.is_valid())
        mocked_submit.assert_called_once()
        self.assertEqual(form.cleaned_data["url"], test_url)

    def test_form_not_valid_on_wrong_url(self):

        form = YoutubeUrlForm(data={"url": "https://www.google.com"})
        
        self.assertFalse(form.is_valid()) 
        self.assertEqual(form.cleaned_data.get("url"), None)

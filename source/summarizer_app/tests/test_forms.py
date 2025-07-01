from django.test import TestCase
from summarizer_app.forms import YoutubeUrlForm
from unittest.mock import patch
from django_recaptcha.client import RecaptchaResponse


def custom_recaptcha_response(score: float) -> RecaptchaResponse:
    """
    method used to create custom RecaptchaResponse object.

    Args:
        score (float): the score of the captcha response.

    Returns: RecaptchaResponse object.
    """

    return RecaptchaResponse(
        is_valid=True,
        extra_data={"score": score},
        action="youtube_url_form"  # this must match the action declared in the form's captcha field
    )


@patch("django_recaptcha.fields.client.submit")
class YoutubeURLFormTests(TestCase):
    """
    Tests for Youtube url form.
    """

    def test_form_validates_youtube_url(self, mocked_submit):

        mocked_submit.return_value = custom_recaptcha_response(score=0.9) # valid captcha

        test_url = "https://www.youtube.com/watch?v=5bId3N7QZec"
        form = YoutubeUrlForm(data={"url": test_url, "captcha": "PASSED"})
        
        self.assertTrue(form.is_valid())
        mocked_submit.assert_called_once()
        self.assertEqual(form.cleaned_data["url"], test_url)

    def test_form_invalid_on_wrong_url(self, mocked_submit):

        mocked_submit.return_value = custom_recaptcha_response(score=0.9) # valid captcha

        form = YoutubeUrlForm(data={"url": "https://www.google.com"})
        
        self.assertFalse(form.is_valid())
        self.assertEqual(form.cleaned_data.get("url"), None)

    def test_form_invalid_on_wrong_captcha(self, mocked_submit):

        mocked_submit.return_value = custom_recaptcha_response(score=0.2) # invalid captcha

        test_url = "https://www.youtube.com/watch?v=5bId3N7QZec"
        form = YoutubeUrlForm(data={"url": test_url, "captcha": "PASSED"})

        self.assertFalse(form.is_valid())
        mocked_submit.assert_called_once()

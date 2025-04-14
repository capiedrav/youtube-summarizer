from django.test import TestCase
from summarizer_app.forms import YoutubeUrlForm


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

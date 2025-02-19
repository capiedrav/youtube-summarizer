from django.test import TestCase
from .views import UrlView
from django.test import SimpleTestCase, Client
from django.urls import reverse, resolve
from .utils import get_video_id, WrongUrlError


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

from django.test import TestCase
from .views import UrlView
from django.test import SimpleTestCase, Client
from django.urls import reverse, resolve


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
        




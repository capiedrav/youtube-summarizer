from django.test import override_settings, TestCase, Client
from django.urls import path, reverse
from project_config.urls import urlpatterns as project_urls

#*************************************************
# These tests are not associated with any app
# That's why they're defined at the project level
#*************************************************

# 1. Define a view that is guaranteed to raise an error
def error_view(request):
    raise Exception("This is a forced 500 error for testing")

# 2. Add this view to a temporary URL conf
urlpatterns = project_urls + [
    path('force-500/', error_view, name="server-error"),
]

# 3. Override settings to use the temp URLs and ensure DEBUG is False
@override_settings(ROOT_URLCONF=__name__, DEBUG=False)
class ServerErrorTests(TestCase):

    def setUp(self):

        self.client = Client(raise_request_exception=False) # client allows exceptions to bubble up to the response
                                                            # rather than crashing the test runner.

    def test_custom_500_page_is_rendered_when_a_view_crashes(self):

        response = self.client.get(reverse("server-error"))

        self.assertTemplateUsed(response, '500.html')
        self.assertContains(response, "Oops!...Something went wrong. Try again later.", status_code=500)

    def test_wrong_url_renders_custom_404_error_page(self):

        response = self.client.get("/wrong-url/")

        self.assertTemplateUsed(response, "404.html")
        self.assertContains(response, "Oops!...You are lost!", status_code=404)
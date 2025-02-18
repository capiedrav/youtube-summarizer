from django.views.generic import TemplateView


class HomeView(TemplateView):
    """
    View for home page.
    """

    template_name = "home.html"
from django.views.generic.edit import FormView
from django.views import View
from django.shortcuts import redirect, reverse, HttpResponseRedirect
from .utils import get_video_id, get_video_summary
from .forms import YoutubeUrlForm

# Create your views here.
class UrlView(FormView):

    template_name = "summarizer_app/home.html"
    form_class = YoutubeUrlForm
    # success_url = reverse("video_summary")

    # def post(self, request):

    #     video_id = get_video_id(request.POST["youtubeUrl"])
    #     video_summary = get_video_summary(video_id)
                
    #     return redirect("home")

    def form_valid(self, form):

        return HttpResponseRedirect(reverse("video_summary"))

    def form_invalid(self, form):

        return HttpResponseRedirect(reverse("video_summary"))

class VideoSummaryView(View):
    pass




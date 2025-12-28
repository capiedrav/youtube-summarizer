from django.views.generic import DetailView, ListView
from django.views.generic.edit import FormView
from django.shortcuts import redirect, reverse
from .models import YTSummary
from .youtube import get_video_id
from .forms import YoutubeUrlForm
import logging
import json


logger = logging.getLogger(__name__)

# Create your views here.
class UrlView(FormView):
    """
    View for rendering home page and handling form submission.
    """

    template_name = "summarizer_app/home.html"
    form_class = YoutubeUrlForm

    def form_valid(self, form):

        # context = self.get_context_data(form=form)
        youtube_url = form.cleaned_data["url"]
        video_id = get_video_id(youtube_url)

        # if a new video summary
        if not YTSummary.summaries.filter(video_id=video_id).exists():
            try: # create the summary
                yt_summary = YTSummary.summaries.create(youtube_url=youtube_url)
            except Exception as e: # log any exception
                logger.error(msg=f"{type(e).__name__} {form.cleaned_data['url']}")
                raise e
        else: # retrieve the summary stored in the database
            yt_summary = YTSummary.summaries.get(video_id=video_id)

        return redirect(yt_summary)
    

class VideoSummaryView(DetailView):
    """
    View for rendering video summary.
    """

    model = YTSummary
    template_name = "summarizer_app/video_summary.html"
    context_object_name = "yt_summary"

    def get_context_data(self, **kwargs):

        context = super().get_context_data(**kwargs)
        context["video_summary"] = json.loads(self.object.video_summary) # video summary as a dict

        return context

class VideoSummaryListView(ListView):
    """
    View for rendering list of video summaries.
    """

    model = YTSummary
    template_name = "summarizer_app/video_summaries.html"
    context_object_name = "yt_summaries"
    queryset = YTSummary.summaries.order_by("-created_on") # summaries ordered from most recent backwards

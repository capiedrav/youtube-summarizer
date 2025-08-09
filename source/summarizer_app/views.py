from django.views.generic import DetailView
from django.views.generic.edit import FormView
from django.shortcuts import redirect, reverse
from .models import YTSummary
from .utils import get_video_id, get_video_summary
from .forms import YoutubeUrlForm
import logging


logger = logging.getLogger(__name__)

# Create your views here.
class UrlView(FormView):

    template_name = "summarizer_app/home.html"
    form_class = YoutubeUrlForm

    def form_valid(self, form):

        context = self.get_context_data(form=form)
        youtube_url = form.cleaned_data["url"]
        video_id = get_video_id(youtube_url)

        # check if a summary of the video already exists in the database
        yt_summary, new_video_summary = YTSummary.objects.get_or_create(
            video_id=video_id,
            defaults={
                # title and thumbnail fields have default values, so they're not defined here
                "url": form.cleaned_data["url"],
                "video_text": "UPDATE ME!!",
                "video_summary": "UPDATE ME!!"
            })

        if new_video_summary: # a summary of the video do not exist in the database
            try:
                video_summary, video_text, title, thumbnail = get_video_summary(youtube_url)
            except Exception as e: # log any exception
                logger.error(msg=f"{type(e).__name__} {form.cleaned_data['url']}")
                raise e
            else:
                yt_summary.video_summary = video_summary
                yt_summary.video_text = video_text
                yt_summary.title = title
                yt_summary.thumbnail = thumbnail
                yt_summary.save()

        context["video_summary"] = yt_summary.video_summary

        return redirect(reverse("video_summary", kwargs={"pk": video_id}))
    

class VideoSummaryView(DetailView):

    model = YTSummary
    template_name = "summarizer_app/video_summary.html"
    context_object_name = "yt_summary"
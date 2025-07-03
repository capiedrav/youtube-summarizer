from django.views.generic import DetailView
from django.views.generic.edit import FormView
from django.shortcuts import redirect, reverse
from .models import YTSummary
from .utils import get_video_id, get_video_summary, EmptyTranscriptError
from .forms import YoutubeUrlForm
from youtube_transcript_api._errors import RequestBlocked
import logging
from django.http import HttpResponseServerError


logger = logging.getLogger(__name__)

# Create your views here.
class UrlView(FormView):

    template_name = "summarizer_app/home.html"
    form_class = YoutubeUrlForm

    def form_valid(self, form):

        context = self.get_context_data(form=form)
        video_id = get_video_id(form.cleaned_data["url"])

        # check if a summary of the video already exists in the database
        yt_summary, created = YTSummary.objects.get_or_create(
            video_id=video_id,
            defaults={
                "url": form.cleaned_data["url"],
                "video_text": "UPDATE ME!!",
                "video_summary": "UPDATE ME!!"
            })

        if created: # a summary of the video do not exist in the database
            try:
                video_summary, video_text = get_video_summary(video_id)
            except (EmptyTranscriptError, RequestBlocked) as e:
                logger.error(msg=type(e).__name__, exc_info=False)
                raise e
            else:
                yt_summary.video_summary = video_summary
                yt_summary.video_text = video_text
                yt_summary.save()

        context["video_summary"] = yt_summary.video_summary

        return redirect(reverse("video_summary", kwargs={"pk": video_id}))
    

class VideoSummaryView(DetailView):

    model = YTSummary
    template_name = "summarizer_app/video_summary.html"
    context_object_name = "yt_summary"
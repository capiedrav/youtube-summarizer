from http.client import HTTPResponse

from django.views.generic import DetailView
from django.views.generic.edit import FormView
from django.shortcuts import redirect, reverse
from .models import YTSummary
from .utils import get_video_id, get_video_summary, EmptyTranscriptError
from .forms import YoutubeUrlForm
from youtube_transcript_api._errors import RequestBlocked
import logging
from asgiref.sync import sync_to_async


logger = logging.getLogger(__name__)

# Create your views here.
class UrlView(FormView):

    template_name = "summarizer_app/home.html"
    form_class = YoutubeUrlForm

    async def get(self, request, *args, **kwargs):

        return self.render_to_response(self.get_context_data())

    async def post(self, request, *args, **kwargs):

        form = self.get_form()
        if form.is_valid():
            return await self.form_valid(form)
        else:
            return self.form_invalid(form)

    async def put(self, *args, **kwargs):

        return self.post(*args, **kwargs)


    async def form_valid(self, form):

        context = self.get_context_data(form=form)
        video_id = get_video_id(form.cleaned_data["url"])

        # check if a summary of the video already exists in the database
        yt_summary, created = await YTSummary.objects.aget_or_create(
            video_id=video_id,
            defaults={
                "url": form.cleaned_data["url"],
                "video_text": "UPDATE ME!!",
                "video_summary": "UPDATE ME!!"
            })

        if created: # a summary of the video do not exist in the database
            try:
                video_summary, video_text = await get_video_summary(video_id)
            except Exception as e: # log any exception
                logger.error(msg=f"{type(e).__name__} {form.cleaned_data['url']}")
                raise e
            else:
                yt_summary.video_summary = video_summary
                yt_summary.video_text = video_text
                await yt_summary.asave()

        context["video_summary"] = yt_summary.video_summary

        return redirect(reverse("video_summary", kwargs={"pk": video_id}))
    

class VideoSummaryView(DetailView):

    model = YTSummary
    template_name = "summarizer_app/video_summary.html"
    context_object_name = "yt_summary"
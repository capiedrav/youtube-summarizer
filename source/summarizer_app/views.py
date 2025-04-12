
from django.views.generic.edit import FormView
from django.views import View
from django.shortcuts import redirect, reverse, HttpResponseRedirect

from .models import YTSummary
from .utils import get_video_id, get_video_summary
from .forms import YoutubeUrlForm

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
                "video_text": "bla bla",
                "video_summary": "bla bla"
            })

        if created: # a summary of the video do not exist in the database
            yt_summary.video_summary = get_video_summary(video_id)
            yt_summary.save()

        context["video_summary"] = yt_summary.video_summary

        return self.render_to_response(context=context)
    

class VideoSummaryView(View):
    pass

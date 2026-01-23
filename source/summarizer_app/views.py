from django.http import HttpResponse
from django.views.generic import DetailView, ListView, TemplateView
from django.views.generic.edit import FormView
from django.shortcuts import redirect, reverse
from .models import YTSummary
from .tasks import trigger_create_summary
from .youtube import get_video_id
from .forms import YoutubeUrlForm
import logging
import json
from celery.result import AsyncResult


logger = logging.getLogger(__name__)

# Create your views here.
class UrlView(FormView):
    """
    View for rendering home page and handling form submission.
    """

    template_name = "summarizer_app/home.html"
    form_class = YoutubeUrlForm

    def form_valid(self, form):

        youtube_url = form.cleaned_data["url"]
        video_id = get_video_id(youtube_url)

        # if a new video summary
        if not YTSummary.summaries.filter(video_id=video_id).exists():
            # create the summary (running a celery task)
            result = trigger_create_summary(youtube_url)

            # move to waiting page
            return redirect(reverse("check-status", kwargs={"task_id": result.task_id}))
        else: # it is a stored summary, retrieve it from the database
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


class CheckStatusView(TemplateView):

    template_name = "summarizer_app/check_status.html"

    def get(self, request, *args, **kwargs):
        """
        Responds to GET requests.
        """

        if request.headers.get("HX-Request") == "true": # GET request coming from HTMX element
            task_id = kwargs["task_id"]
            result = AsyncResult(task_id)

            if result.state == "SUCCESS":
                # redirect to video summary using HTMX
                response = HttpResponse()
                response["HX-Redirect"] = reverse("video-summary", kwargs={"pk": task_id})

                return response

            elif result.state == "FAILURE":
                # redirect to server error page using HTMX
                response = HttpResponse()
                response.status_code = 200
                response["HX-Redirect"] = reverse("celery-error")

                return response

            else: # task not done yet (e.g. in PENDING state)
                # send empty response
                response = HttpResponse()
                response.status_code = 200

                return response

        return super().get(request, *args, *kwargs) # render check_status.html

    def get_context_data(self, **kwargs):

        context = super().get_context_data(**kwargs)
        context["task_id"] = self.kwargs["task_id"] # task_id is available in check_status.html template

        return context

        
class CeleryErrorView(TemplateView):
    """
    This class displays 500 error page when celery task fails.
    """

    template_name = "500.html"

    def get(self, request, *args, **kwargs):

        response = super().get(request, *args, **kwargs)

        response.status_code = 500 # signal a server error

        return response
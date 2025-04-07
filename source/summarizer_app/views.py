from django.views.generic.edit import FormView
from django.views import View
from django.shortcuts import redirect, reverse, HttpResponseRedirect
from .utils import get_video_id, get_video_summary
from .forms import YoutubeUrlForm

# Create your views here.
class UrlView(FormView):

    template_name = "summarizer_app/home.html"
    form_class = YoutubeUrlForm
    
    def form_valid(self, form):
        context = self.get_context_data(form=form)
        
        video_id = get_video_id(form.cleaned_data["url"])
        context["video_summary"] = get_video_summary(video_id)

        return self.render_to_response(context=context)
    

class VideoSummaryView(View):
    pass




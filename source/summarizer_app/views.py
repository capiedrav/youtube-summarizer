from django.views import View
from django.shortcuts import redirect
from .utils import get_video_id


# Create your views here.
class UrlView(View):

    def post(self, request):

        videoId = get_video_id(request.POST["youtubeUrl"])

        print(videoId)
        return redirect("home")






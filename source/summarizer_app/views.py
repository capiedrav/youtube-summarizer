from django.views import View
from django.shortcuts import redirect

# Create your views here.
class UrlView(View):

    def post(self, request):

        # print(request.__dict__)
        return redirect("home")






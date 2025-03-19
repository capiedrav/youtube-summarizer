from django import forms

class YoutubeUrlForm(forms.Form):

    url = forms.URLField()

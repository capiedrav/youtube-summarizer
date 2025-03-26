from django import forms
from django.core.validators import RegexValidator
from django.utils.translation import gettext_lazy as _

 
class YoutubeUrlForm(forms.Form):

    youtube_url_validator = RegexValidator(
        regex=r"^(https?://)?(www\.)?(youtube\.com|youtu\.be)/(watch\?v=)([a-z|A-Z|0-9]+$)",
        message=_("Enter a valid youtube url.")
    )
    
    url = forms.URLField(validators=[youtube_url_validator, ])

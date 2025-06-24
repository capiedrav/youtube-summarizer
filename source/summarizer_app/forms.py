from django import forms
from django.core.validators import RegexValidator
from django.utils.translation import gettext_lazy as _
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Fieldset, Submit, Field, Div
from django_recaptcha.fields import ReCaptchaField
from django_recaptcha.widgets import ReCaptchaV3

 
youtube_url_validator = RegexValidator(
        regex=r"^(https?://)?(www\.)?(youtube\.com|youtu\.be)/(watch\?v=)([a-z]|[A-Z]|[0-9]|[\-_])+$",
        message=_("Enter a valid youtube url.")
    )


class YoutubeUrlForm(forms.Form):
       
    url = forms.URLField(label="Enter Youtube Video URL", validators=[youtube_url_validator, ])
    captcha = ReCaptchaField(widget=ReCaptchaV3(action="youtube_url_form"))

    def __init__(self, *args, **kwargs):

        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = "post"
        self.helper.form_action = "home"
        self.helper.form_class = "d-flex flex-column align-items-md-start align-items-center"
        self.helper.form_id = "yt-form"
        self.helper.layout = Layout(
            Field(
                "url",
                css_class="form-control shadow",
                wrapper_class="align-self-stretch",
                placeholder="https://www.youtube.com/watch?v=...",
                id="youtubeUrl",
                pattern="^(https?://)?(www\.)?(youtube\.com|youtu\.be)/(watch\?v=)([a-z|A-Z|0-9]+$)",
                required="true"
            ),
            Field("captcha"),
            Submit(name="submit", value="Summarize Video")
        )

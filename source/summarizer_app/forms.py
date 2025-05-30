from django import forms
from django.core.validators import RegexValidator
from django.utils.translation import gettext_lazy as _
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Fieldset, Submit, Field, Div

 
youtube_url_validator = RegexValidator(
        regex=r"^(https?://)?(www\.)?(youtube\.com|youtu\.be)/(watch\?v=)([a-z]|[A-Z]|[0-9]|[\-_])+$",
        message=_("Enter a valid youtube url.")
    )


class YoutubeUrlForm(forms.Form):
       
    url = forms.URLField(label="Enter Youtube Video URL", validators=[youtube_url_validator, ])

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
            Submit(name="submit", value="Summarize Video")
        )

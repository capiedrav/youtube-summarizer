from django.db import models
from .forms import youtube_url_validator


class YTSummary(models.Model):

    video_id = models.CharField(max_length=22, primary_key=True, default=None, null=False)
    url = models.URLField(validators=[youtube_url_validator, ], default=None, null=False)
    video_text = models.TextField(default=None, null=False)
    video_summary = models.TextField(default=None, null=False)    
    created_on = models.DateField(auto_now=True)
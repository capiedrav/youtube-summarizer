from django.db import models
from .forms import youtube_url_validator


class YTSummary(models.Model):

    video_id = models.CharField(max_length=22, primary_key=True, default=None, null=False)
    url = models.URLField(validators=[youtube_url_validator, ], default=None, null=False)
    title = models.CharField(max_length=255, default="Title Not Available", null=False)
    thumbnail = models.ImageField(default="thumbnails/thumbnail_not_found.jpg", null=False) # this path is relative to
                                                                                            # MEDIA_ROOT in settings.py
    video_text = models.TextField(default=None, null=False)
    video_summary = models.TextField(default=None, null=False)    
    created_on = models.DateTimeField(auto_now=True)

    def save(self, force_insert = ..., force_update = ..., using = ..., update_fields = ...,):
        """
        Override this method to make sure url field is valid before saving.
        """

        self.full_clean() # this method checks that all model fields are valid, if not, it raises ValidationError
        super().save()

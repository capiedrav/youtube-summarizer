from django.db import models
from .forms import youtube_url_validator
from django.urls import reverse
from .summary import get_video_summary


class YTSummaryManager(models.Manager):

    def create(self, youtube_url: str) -> "YTSummary":

        video_id, video_summary, video_text, video_title, video_thumbnail = get_video_summary(youtube_url)

        yt_summary = self.model(
            video_id=video_id,
            url=youtube_url,
            title=video_title,
            thumbnail=video_thumbnail,
            video_text=video_text,
            video_summary=video_summary
        )
        yt_summary.save()

        return yt_summary

class YTSummary(models.Model):

    video_id = models.CharField(max_length=22, primary_key=True, default=None, null=False)
    url = models.URLField(validators=[youtube_url_validator, ], default=None, null=False)
    title = models.CharField(max_length=255, default="Title Not Available", null=False)
    thumbnail = models.ImageField(default="thumbnails/thumbnail_not_found.jpg", null=False) # this path is relative to
                                                                                            # MEDIA_ROOT in settings.py
    video_text = models.TextField(default=None, null=False)
    video_summary = models.TextField(default=None, null=False) # the summaries are stored as json strings
    created_on = models.DateTimeField(auto_now_add=True)
    summaries = YTSummaryManager() # default object manager

    class Meta:
        verbose_name_plural = "YTSummaries"

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse(viewname="video-summary", kwargs={"pk": self.video_id})

    def save(self, force_insert = ..., force_update = ..., using = ..., update_fields = ...,):
        """
        Override this method to make sure url field is valid before saving.
        """

        self.full_clean() # this method checks that all model fields are valid, if not, it raises ValidationError
        super().save()

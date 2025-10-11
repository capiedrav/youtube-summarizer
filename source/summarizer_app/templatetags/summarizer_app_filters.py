from django import template
import json


register = template.Library()


@register.filter(is_safe=True)
def get_overview(video_summary: str) -> str:
    """
    This filter extracts the overview value from a video summary (as a json string) and returns it.

    This is used in video_summaries.html to display the overview of each video summary.
    """

    overview = "Overview not available."
    try:
        video_summary = json.loads(video_summary) # from json string to dict
        overview = video_summary["overview"]
    except (json.decoder.JSONDecodeError, KeyError):
        pass

    return overview





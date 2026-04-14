from typing import Callable, Any
from requests import Response
from youtube_transcript_api import YouTubeTranscriptApi as YTA, YouTubeTranscriptApi
from youtube_transcript_api.proxies import GenericProxyConfig
from youtube_transcript_api.formatters import TextFormatter
from pytubefix import YouTube
import requests
from django.conf import settings
import logging
import shutil
import os

logger = logging.getLogger(__name__)

# proxy provided by dataimpulse
proxy_username = os.getenv("PROXY_USERNAME", default="no_username")
proxy_password = os.getenv("PROXY_PASSWORD", default="no_password")
proxy_port = os.getenv("PROXY_PORT", default="8080")
proxies = { # proxies urls
    "http": f"http://{proxy_username}:{proxy_password}@gw.dataimpulse.com:{proxy_port}",
    "https": f"http://{proxy_username}:{proxy_password}@gw.dataimpulse.com:{proxy_port}",
}

def get_yta() -> YouTubeTranscriptApi:
    """
    Get a YoutubeTranscriptApi instance configured with proxies and ready to use.
    """

    return YTA(# config youtube-transcript-api using dataimpulse proxy credentials
        proxy_config=GenericProxyConfig(
            http_url=proxies.get("http", ""),
            https_url=proxies.get("https", ""),
        )
    )

class WrongUrlError(Exception):
    pass


def _try_three_times(function: Callable, **kwargs) -> Any:
    """
    Tries to execute 'function' three times if the function fails for any reason.
    After the three failed attempts, this function raise the error.
    Args:
        function (Callable): function to be executed.
        **kwargs: arguments to be passed to the function.

    Returns (Any): the result of calling 'function'.
    """

    for i in range(3):
        try:
            return function(**kwargs)
        except Exception as error:
            logger.error(msg=f"{type(error).__name__} {error}")
            if i == 2:
                raise error

    return None

def get_video_id(youtube_url: str) -> str:
    """
    Returns the video id of a youtube url. For example, the video id of the following url

    https://www.youtube.com/watch?v=5bId3N7QZec

    is:

    5bId3N7QZec

    Args:
        youtube_url (string): youtube url

    Returns:
        video_id (string): video id
    """

    split_url = youtube_url.split("v=")

    if len(split_url) == 2:
        video_id = split_url[1]
        if video_id:
            return video_id

    raise WrongUrlError(f"{youtube_url} is not a valid youtube url")


def get_video_text(video_id: str) -> str:

    ytt_api = get_yta()

    video_transcript = _try_three_times(ytt_api.fetch, video_id=video_id)  # get video transcript

    # format transcript as text
    text_formater = TextFormatter()
    video_text = text_formater.format_transcript(video_transcript)

    return video_text

def get_video_title(youtube_url: str) -> str | None:

    yt = YouTube(url=youtube_url, proxies=proxies)
    return _try_three_times(lambda: yt.title) # wrap title property in a lambda function to avoid immediate evaluation

def _get_thumbnail_url(youtube_url: str) -> str:
    """
    Helper function used in get_video_thumbnail function.

    Args:
        youtube_url:

    Returns:
        (str) thumbnail url.
    """

    yt = YouTube(url=youtube_url, proxies=proxies)
    return _try_three_times(lambda: yt.thumbnail_url) # wrap thumbnail_url property in a lambda function to
                                                      # avoid immediate evaluation

def _get_thumbnail_image(thumbnail_url: str) -> Response:
    """
    Helper function used in get_video_thumbnail function.

    Returns:
         The thumbnail image data in a Response object.
    """

    return _try_three_times(requests.get, url=thumbnail_url, proxies=proxies, stream=True)

def _save_thumbnail_image(response: Response, video_id: str) -> str:
    """
    Helper function used in get_video_thumbnail function.
    Saves the thumbnail image data as an image file.

    Returns:
        (str) path to where the thumbnail is saved (path relative to settings.MEDIA_ROOT).
    """

    # absolute path to where the thumbnail is stored
    thumbnail_path = (settings.THUMBNAILS_PATH / f"{video_id}.jpg").resolve().as_posix()
    with open(thumbnail_path, "wb") as file:  # save thumbnail
        response.raw.decode_content = True
        shutil.copyfileobj(response.raw, file)

    return f"thumbnails/{video_id}.jpg"  # path relative to settings.MEDIA_ROOT

def get_video_thumbnail(youtube_url: str) -> str | None:
    """
    Does the overall process of getting a video thumbnail.
    Args:
        youtube_url: youtube url

    Returns:
        (str | None) path to where the thumbnail is saved (path relative to settings.MEDIA_ROOT).
    """

    thumbnail_url = _get_thumbnail_url(youtube_url)
    response = _get_thumbnail_image(thumbnail_url)

    if response.status_code == 200:
        video_id = get_video_id(youtube_url)
        return _save_thumbnail_image(response, video_id)

    return None
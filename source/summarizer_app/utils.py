import shutil
from youtube_transcript_api import YouTubeTranscriptApi as YTA
from youtube_transcript_api.proxies import GenericProxyConfig, WebshareProxyConfig
from youtube_transcript_api.formatters import TextFormatter
from youtube_transcript_api._errors import RequestBlocked, CouldNotRetrieveTranscript
from openai import OpenAI
import os
from xml.etree.ElementTree import ParseError
from xml.parsers.expat import ExpatError
from pytubefix import YouTube
import requests
from django.conf import settings

# concat '-rotate' to PROXY_USERNAME for automatic proxy ip address rotation
proxy_username = os.getenv("PROXY_USERNAME") + "-rotate"
proxy_password = os.getenv("PROXY_PASSWORD")
pytubefix_proxies = {
    "http": f"http://{proxy_username}:{proxy_password}@p.webshare.io:80",
    "https": f"http://{proxy_username}:{proxy_password}@p.webshare.io:80",
}


class WrongUrlError(Exception):
    pass

class EmptyTranscriptError(CouldNotRetrieveTranscript):
    CAUSE_MESSAGE = (
        "Request to YouTube was successful, but the response's content is empty, "
        "so the transcript parsing cannot be performed. "
        "Retry later."
    )


def get_video_id(youtube_url:str) -> str:
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

    ytt_api = YTA( # config youtube-transcript-api using Webshare proxy credentials
        proxy_config=WebshareProxyConfig(
            proxy_username=os.environ.get("PROXY_USERNAME"),
            proxy_password=os.environ.get("PROXY_PASSWORD")
        )
    )

    # try three times to get the video transcript if the request is blocked
    for i in range(3):
        try:
            video_transcript = ytt_api.fetch(video_id=video_id)
        except RequestBlocked as error:
            if i == 2:
                raise error
        except (ExpatError, ParseError):
            # This issue is discussed in:
            # https://github.com/jdepoix/youtube-transcript-api/issues/414
            # https://github.com/jdepoix/youtube-transcript-api/issues/320
            # These errors should be solved with the new version of youtube-transcript-api
            # but just in case they appear again
             raise EmptyTranscriptError(video_id)
        else:
            break

    # format transcript as text
    text_formater = TextFormatter()
    video_text = text_formater.format_transcript(video_transcript)
        
    return video_text

def get_text_summary(text: str) -> str:
    
    # setup deepseek client using openai sdk
    deepseek_client = OpenAI(api_key=os.environ.get("DEEPSEEK_API_KEY"), base_url="https://api.deepseek.com")

    messages = [        
        {
            "role": "system",
            "content": "You are an experienced editor that can summarize text very well."
        },
        {
            "role": "user",
            "content": f"{text}\n\nPlease summarize the key information of video transcript."
        }        
    ]

    # call deepseek api passing the messages prompt
    response = deepseek_client.chat.completions.create(
        model="deepseek-chat",
        messages=messages,
        stream=False
    )

    # return the api response
    return response.choices[0].message.content

def get_video_title(youtube_url: str) -> str:

    return YouTube(url=youtube_url, proxies=pytubefix_proxies).title

def get_video_thumbnail(youtube_url: str) -> str | None:

    thumbnail_url = YouTube(url=youtube_url, proxies=pytubefix_proxies).thumbnail_url
    response = requests.get(thumbnail_url, proxies=pytubefix_proxies, stream=True)

    if response.status_code == 200:
        video_id = get_video_id(youtube_url)
        thumbnail_path = (settings.THUMBNAILS_PATH / f"{video_id}.jpg").resolve().as_posix()
        with open(thumbnail_path, "wb") as file:
            response.raw.decode_content = True
            shutil.copyfileobj(response.raw, file)

        return thumbnail_path

    return None


def get_video_summary(youtube_url: str) -> tuple[str, str,str, str | None]:

    video_id = get_video_id(youtube_url)
    video_text = get_video_text(video_id)
    video_summary = get_text_summary(video_text)
    video_title = get_video_title(youtube_url)
    video_thumbnail = get_video_thumbnail(youtube_url)

    return video_summary, video_text, video_title, video_thumbnail
    
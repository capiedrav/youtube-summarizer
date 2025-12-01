import shutil
from typing import Callable, Any
from youtube_transcript_api import YouTubeTranscriptApi as YTA
from youtube_transcript_api.proxies import WebshareProxyConfig
from youtube_transcript_api.formatters import TextFormatter
from langchain_deepseek import ChatDeepSeek
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import JsonOutputParser
import json
from pydantic import BaseModel, Field
import os
from pytubefix import YouTube
import requests
from django.conf import settings

# concat '-rotate' to PROXY_USERNAME for automatic proxy ip address rotation
proxy_username = os.getenv("PROXY_USERNAME", default="no_username") + "-rotate"
proxy_password = os.getenv("PROXY_PASSWORD", default="no_password")
pytubefix_proxies = {
    "http": f"http://{proxy_username}:{proxy_password}@p.webshare.io:80",
    "https": f"http://{proxy_username}:{proxy_password}@p.webshare.io:80",
}


class WrongUrlError(Exception):
    pass


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
            if i == 2:
                raise error

    return None

def get_video_text(video_id: str) -> str:

    ytt_api = YTA( # config youtube-transcript-api using Webshare proxy credentials
        proxy_config=WebshareProxyConfig(
            proxy_username=os.environ.get("PROXY_USERNAME"),
            proxy_password=os.environ.get("PROXY_PASSWORD")
        )
    )

    video_transcript = _try_three_times(ytt_api.fetch, video_id=video_id) # get video transcript

    # format transcript as text
    text_formater = TextFormatter()
    video_text = text_formater.format_transcript(video_transcript)
        
    return video_text


class Summary(BaseModel):
    """
    This is the template for the JSON object expected from the llm.
    """

    overview: str = Field(description="A high-level overview of the main topic and key points discussed.")
    key_takeaways: list[str] = Field(description="A list of the most important insights, facts, or steps.")
    conclusion: str = Field(
        description="A concise wrap-up of the video's overall message or next steps (if any), highlighting the \
                     core value or outcome."
    )

def get_text_summary(text: str) -> str:

    json_parser = JsonOutputParser(pydantic_object=Summary)
    prompt = PromptTemplate.from_template(
        template="""
            Summarize the following video transcript clearly and concisely.

            {parser_instructions}

            Be concise but informative. Preserve the original intent and tone of the speaker.
            Don't include filler or irrelevant content.

            Transcript: {transcript}
        """
    )

    llm = ChatDeepSeek(model="deepseek-chat", temperature=0.1)
    summarizer = prompt | llm | json_parser
    response = summarizer.invoke(
        input={"parser_instructions": json_parser.get_format_instructions(), "transcript": text}
    )

    return json.dumps(response) # response as a json string

def get_video_title(youtube_url: str) -> str | None:

    yt = YouTube(url=youtube_url, proxies=pytubefix_proxies)
    return _try_three_times(lambda: yt.title) # wrap title property in a lambda function to avoid immediate evaluation

def get_thumbnail_url(youtube_url: str) -> str:

    yt = YouTube(url=youtube_url, proxies=pytubefix_proxies)
    return _try_three_times(lambda: yt.thumbnail_url) # wrap thumbnail_url property in a lambda function to
                                                      # avoid immediate evaluation

def get_video_thumbnail(youtube_url: str) -> str | None:

    thumbnail_url = get_thumbnail_url(youtube_url)

    response = _try_three_times(requests.get, url=thumbnail_url, proxies=pytubefix_proxies, stream=True)

    if response.status_code == 200:
        video_id = get_video_id(youtube_url)
        # absolute path to where the thumbnail is stored
        thumbnail_path = (settings.THUMBNAILS_PATH / f"{video_id}.jpg").resolve().as_posix()
        with open(thumbnail_path, "wb") as file: # save thumbnail
            response.raw.decode_content = True
            shutil.copyfileobj(response.raw, file)

        return f"thumbnails/{video_id}.jpg" # path relative to settings.MEDIA_ROOT

    return None

def get_video_summary(youtube_url: str) -> tuple[str, str,str, str | None]:

    video_id = get_video_id(youtube_url)
    video_text = get_video_text(video_id)
    video_summary = get_text_summary(video_text)
    video_title = get_video_title(youtube_url)
    video_thumbnail = get_video_thumbnail(youtube_url)

    return video_summary, video_text, video_title, video_thumbnail
    
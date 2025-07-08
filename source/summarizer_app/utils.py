from youtube_transcript_api import YouTubeTranscriptApi as YTA
from youtube_transcript_api.proxies import WebshareProxyConfig
from youtube_transcript_api.formatters import TextFormatter
from youtube_transcript_api._errors import RequestBlocked, CouldNotRetrieveTranscript
from openai import AsyncOpenAI
import os
from xml.etree.ElementTree import ParseError
from xml.parsers.expat import ExpatError
from asgiref.sync import sync_to_async


class WrongUrlError(Exception):
    pass


class EmptyTranscriptError(CouldNotRetrieveTranscript):
    CAUSE_MESSAGE = (
        "Request to YouTube was successful, but the response's content is empty, "
        "so the transcript parsing cannot be performed. "
        "Retry later."
    )


def get_video_id(youtubeUrl:str) -> str:
    """
    Returns the video id of a youtube url. For example, the video id of the following url 
    
    https://www.youtube.com/watch?v=5bId3N7QZec

    is:

    5bId3N7QZec
    
    Args:
        youtubeUrl (string): youtube url

    Returns:
        video_id (string): video id

    """
    
    split_url = youtubeUrl.split("v=")
    
    if len(split_url) == 2:
        video_id = split_url[1]
        if video_id:
            return video_id

    raise WrongUrlError(f"{youtubeUrl} is not a valid youtube url")    

async def get_video_text(video_id: str) -> str:

    ytt_api = YTA( # config youtube-transcript-api using Webshare proxy credentials
        proxy_config=WebshareProxyConfig(
            proxy_username=os.environ.get("PROXY_USERNAME"),
            proxy_password=os.environ.get("PROXY_PASSWORD")
        )
    )

    async_fetch = sync_to_async(ytt_api.fetch)
    # try three times to get the video transcript if the request is blocked
    for i in range(3):
        try:
            video_transcript = await async_fetch(video_id=video_id)
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

async def get_text_summary(text: str) -> str:
    
    # setup deepseek client using openai sdk
    deepseek_client = AsyncOpenAI(api_key=os.environ.get("DEEPSEEK_API_KEY"), base_url="https://api.deepseek.com")

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
    response = await deepseek_client.chat.completions.create(
        model="deepseek-chat",
        messages=messages,
        stream=False
    )

    # return the api response
    return response.choices[0].message.content

async def get_video_summary(video_id: str) -> tuple[str, str]:

    video_text = await get_video_text(video_id)
    video_summary = await get_text_summary(video_text)

    return video_summary, video_text
    
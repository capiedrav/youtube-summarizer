from fp.fp import FreeProxy
from youtube_transcript_api import YouTubeTranscriptApi as YTA
from youtube_transcript_api.formatters import TextFormatter
from openai import OpenAI
import os


class WrongUrlError(Exception):
    pass


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
    
    splitted_url = youtubeUrl.split("v=")
    
    if len(splitted_url) == 2:
        video_id = splitted_url[1]
        if video_id:
            return video_id

    raise WrongUrlError(f"{youtubeUrl} is not a valid youtube url")    

def get_video_text(video_id: str) -> str:

    # select a random proxy server to avoid blacklisting the server's ip address
    proxy_server = FreeProxy(rand=True).get() 

    # get the video transcript
    video_transcript = YTA.get_transcript(video_id=video_id, proxies={"http": proxy_server})

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

def get_video_summary(video_id: str) -> str:

    video_text = get_video_text(video_id)
    video_summary = get_text_summary(video_text)

    return video_summary
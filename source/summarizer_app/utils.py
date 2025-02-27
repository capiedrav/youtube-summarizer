from fp.fp import FreeProxy
from youtube_transcript_api import YouTubeTranscriptApi as YTA
from youtube_transcript_api.formatters import TextFormatter


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

    # format transcript to text
    text_formater = TextFormatter()
    video_text = text_formater.format_transcript(video_transcript)
    
    return video_text

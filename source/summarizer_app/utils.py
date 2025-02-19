class WrongUrlError(Exception):
    pass


def get_video_id(youtubeUrl):
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
    
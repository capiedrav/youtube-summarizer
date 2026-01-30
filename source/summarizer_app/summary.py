from langchain_deepseek import ChatDeepSeek
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import JsonOutputParser
import json
from pydantic import BaseModel, Field
from .youtube import get_video_id, get_video_thumbnail, get_video_title, get_video_text

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


def get_video_summary(youtube_url: str) -> tuple[str, str,str, str, str | None]:

    video_id = get_video_id(youtube_url)
    video_text = get_video_text(video_id)
    video_summary = get_text_summary(video_text)
    video_title = get_video_title(youtube_url)
    video_thumbnail = get_video_thumbnail(youtube_url)

    return video_id, video_summary, video_text, video_title, video_thumbnail

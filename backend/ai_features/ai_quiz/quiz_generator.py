import json
from openai import AzureOpenAI
from core.config import settings
from .prompts import QUIZ_PROMPT_V1


def generate_quiz(transcript_text: str):
    """
    Generate quiz questions from transcript text.
    Returns list of questions.
    """

    client = AzureOpenAI(
        azure_endpoint=settings.AZURE_OPENAI_ENDPOINT,
        api_key=settings.AZURE_OPENAI_API_KEY,
        api_version=settings.AZURE_OPENAI_API_VERSION
    )

    response = client.chat.completions.create(
        model=settings.AZURE_OPENAI_DEPLOYMENT,
        temperature=0.3,
        messages=[
            {"role": "system", "content": QUIZ_PROMPT_V1},
            {"role": "user", "content": transcript_text[:15000]}
        ],
        response_format={"type": "json_object"}
    )

    content = response.choices[0].message.content
    quiz_data = json.loads(content)

    return quiz_data.get("questions", [])

from openai import AzureOpenAI
from config import AZURE_OPENAI_API_KEY, AZURE_OPENAI_ENDPOINT, AZURE_OPENAI_API_VERSION
import json
from prompts import QUIZ_PROMPT_V1
from datetime import datetime
import uuid

client = AzureOpenAI(
    api_key=AZURE_OPENAI_API_KEY,
    api_version=AZURE_OPENAI_API_VERSION,
    azure_endpoint=AZURE_OPENAI_ENDPOINT
)


class QuizGenerator:

    def generate(self, transcript_text: str):

        response = client.chat.completions.create(
            model="gpt-4o",  # must match your Azure deployment name
            temperature=0.3,
            messages=[
                {"role": "system", "content": QUIZ_PROMPT_V1},
                {"role": "user", "content": transcript_text}
            ],
            response_format={"type": "json_object"}
        )

        content = response.choices[0].message.content
        quiz_data = json.loads(content)

        # Return only questions
        return {
            "questions": quiz_data["questions"]
        }




        response = client.chat.completions.create(
            model="gpt-4o",  # your Azure deployment name
            temperature=0.3,
            messages=[
                {"role": "system", "content": QUIZ_PROMPT_V1},
                {"role": "user", "content": transcript_text}
            ],
            response_format={"type": "json_object"}
        )

        content = response.choices[0].message.content
        quiz_data = json.loads(content)

        asset = {
            "asset_id": str(uuid.uuid4()),
            "type": "quiz",
            "linked_course_id": course_id,
            "linked_module_id": module_id,
            "transcript_blob_url": "local_upload_for_now",
            "questions": quiz_data["questions"],
            "model_used": "gpt-4o",
            "created_at": datetime.utcnow().isoformat()
        }

        return asset
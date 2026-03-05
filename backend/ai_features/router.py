from fastapi import APIRouter, BackgroundTasks, HTTPException, Depends
from core.database import db
from core.security import get_current_user
from backend.courses.services import generate_read_sas
from ai_features.services import run_ai_pipeline
from openai import AzureOpenAI
from core.config import settings

router = APIRouter()

@router.post("/process-video/{video_id}")
async def process_video(
    video_id: str, 
    background_tasks: BackgroundTasks,
    user: dict = Depends(get_current_user)
):
    try:
        # 1. Get Video Details
        doc_ref = db.collection("videos").document(video_id)
        doc = doc_ref.get()
        if not doc.exists:
            raise HTTPException(status_code=404, detail="Video not found")
            
        data = doc.to_dict()
        blob_path = data.get("storage_path")
        
        # 2. Get Fresh Link (Using Backend 2's service logic)
        fresh_sas_url = generate_read_sas(blob_path)
        
        # 3. Trigger Background Task
        background_tasks.add_task(run_ai_pipeline, video_id, fresh_sas_url, data.get("title"))

        return {"message": "AI processing started"}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

def grade_quiz_answer(
        user_answer: str,
        correct_answer: str,
        question_text: str,
        expected_answer_hints: list = None
) -> dict:
    """
    Use Azure OpenAI to grade an answer.

    Args:
        user_answer: Student's answer
        correct_answer: Expected correct answer
        question_text: The question
        expected_answer_hints: List of hints about correct answer

    Returns:
        GradingResult dict with score and feedback
    """
    try:
        client = AzureOpenAI(
            azure_endpoint=settings.AZURE_OPENAI_ENDPOINT,
            api_key=settings.AZURE_OPENAI_API_KEY,
            api_version=settings.AZURE_OPENAI_API_VERSION
        )

        hints_text = "\n".join(expected_answer_hints) if expected_answer_hints else ""

        prompt = f"""
        Grade this student answer on a scale of 0-1.

        Question: {question_text}
        Correct Answer: {correct_answer}
        Answer Hints: {hints_text}
        Student Answer: {user_answer}

        Respond in JSON format:
        {{
            "score": 0.0 to 1.0,
            "correct": true/false,
            "feedback": "explanation of grading"
        }}
        """

        response = client.chat.completions.create(
            model=settings.AZURE_OPENAI_DEPLOYMENT,
            messages=[{"role": "user", "content": prompt}]
        )

        import json
        result = json.loads(response.choices[0].message.content)

        return {
            "question_id": question_text[:50],  # Use first 50 chars as ID
            "correct": result["correct"],
            "user_answer": user_answer,
            "expected_answer": correct_answer,
            "feedback": result.get("feedback", ""),
            "score": result["score"]
        }

    except Exception as e:
        print(f"❌ Grading Error: {str(e)}")
        # Return neutral grading on error
        return {
            "question_id": question_text[:50],
            "correct": False,
            "user_answer": user_answer,
            "expected_answer": correct_answer,
            "feedback": "Error during grading",
            "score": 0.5
        }
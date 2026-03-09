from fastapi import APIRouter, BackgroundTasks, HTTPException, Depends
from core.database import db
from core.security import get_current_user
from courses.services import generate_read_sas
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

@router.post("/submit-quiz")
async def submit_quiz(payload: dict, user: dict = Depends(get_current_user)):
    from ai_features.services import grade_quiz
    # Payload should contain: module_id, answers, etc.
    score, completed = grade_quiz(payload.get("answers", []))
    if completed and payload.get("module_id"):
        db.collection("modules").document(payload["module_id"]).update({"completed": True})
    return {"score": score, "completed": completed}
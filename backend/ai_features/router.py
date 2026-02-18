from fastapi import APIRouter, BackgroundTasks, HTTPException, Depends
from core.database import db
from core.security import get_current_user
from courses.services import generate_read_sas
from ai_features.services import run_ai_pipeline

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
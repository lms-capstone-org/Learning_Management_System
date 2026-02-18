

from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Depends, BackgroundTasks
from datetime import datetime
from firebase_admin import firestore

# Imports from Core
from core.database import db
from core.security import get_current_user
from courses.services import upload_blob, generate_read_sas

# Import the AI Pipeline function
from ai_features.services import run_ai_pipeline

router = APIRouter()

@router.post("/upload")
async def upload_video(
    background_tasks: BackgroundTasks,  # <--- INJECT BACKGROUND TASKS
    file: UploadFile = File(...),
    title: str = Form(...),
    user: dict = Depends(get_current_user) 
):
    try:
        instructor_id = user['uid']
        clean_filename = file.filename.replace(" ", "_")
        timestamp = int(datetime.now().timestamp())
        
        # Path structure: instructors/{uid}/videos/...
        blob_path = f"instructors/{instructor_id}/videos/{timestamp}_{clean_filename}"
        
        # 1. Upload to Azure
        file_content = await file.read()
        upload_blob(file_content, blob_path)
        
        # 2. Generate Link (Needed for Frontend AND for AI to download it)
        sas_url = generate_read_sas(blob_path)

        # 3. Save to Firebase (Old Schema)
        doc_ref = db.collection("videos").document()
        doc_ref.set({
            "title": title,
            "instructor_id": instructor_id,
            "video_url": sas_url,
            "storage_path": blob_path,
            "filename": clean_filename,
            "status": "processing", # <--- Set status to processing immediately
            "created_at": firestore.SERVER_TIMESTAMP,
            "summary": "AI is analyzing this video...", # Placeholder
            "transcript": ""
        })

        # 4. TRIGGER AI AUTOMATICALLY 🚀
        # We pass the doc_id, the SAS URL, and the filename to the AI worker
        background_tasks.add_task(run_ai_pipeline, doc_ref.id, sas_url, clean_filename)

        return {
            "message": "Upload successful. AI processing started automatically.", 
            "video_id": doc_ref.id
        }

    except Exception as e:
        print(f"❌ Upload Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/")
def get_videos(user: dict = Depends(get_current_user)):
    """
    Fetches videos using the Old Schema logic
    """
    docs = db.collection("videos").order_by("created_at", direction=firestore.Query.DESCENDING).stream()
    videos = []
    for doc in docs:
        data = doc.to_dict()
        if "created_at" in data and data["created_at"] is not None:
            data["created_at"] = data["created_at"].isoformat()
        data["id"] = doc.id
        videos.append(data)
    return videos
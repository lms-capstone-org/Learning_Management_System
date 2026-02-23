
from fastapi import APIRouter, UploadFile, File, BackgroundTasks, HTTPException
from datetime import datetime, timedelta
import uuid

# Imports from your project structure
from core.config import settings
from ai_features.services import run_ai_pipeline, blob_service_client  # Importing the client we set up in services

# Import specific Azure Blob types for SAS generation
from azure.storage.blob import generate_blob_sas, BlobSasPermissions

router = APIRouter()


def generate_test_sas(blob_path: str):
    """
    Generates a temporary SAS token so Azure Speech Service can download the video.
    Uses User Delegation Key (AAD Auth).
    """
    try:
        now = datetime.utcnow()
        start_time = now - timedelta(minutes=5)
        expiry_time = now + timedelta(hours=2)  # 2 hours valid for processing

        # Get Delegation Key from Azure (AAD)
        delegation_key = blob_service_client.get_user_delegation_key(
            key_start_time=start_time,
            key_expiry_time=expiry_time
        )

        sas_token = generate_blob_sas(
            account_name=blob_service_client.account_name,
            container_name=settings.BLOB_CONTAINER_NAME,
            blob_name=blob_path,
            user_delegation_key=delegation_key,
            permission=BlobSasPermissions(read=True),
            expiry=expiry_time,
            start=start_time
        )
        return f"{settings.AZURE_STORAGE_ACCOUNT_URL}/{settings.BLOB_CONTAINER_NAME}/{blob_path}?{sas_token}"
    except Exception as e:
        print(f"❌ Error generating SAS: {e}")
        return None


@router.post("/test-upload-pipeline")
async def test_ai_pipeline(
        background_tasks: BackgroundTasks,
        file: UploadFile = File(...)
):
    """
    SANDBOX ENDPOINT:
    1. Generates Dummy Course/Module IDs
    2. Uploads Video to Azure (using AAD)
    3. Generates SAS
    4. Triggers AI Pipeline
    """
    try:
        # 1. Generate Dummy IDs
        fake_course_id = "course_test_AAD_01"
        fake_module_id = f"mod_{uuid.uuid4().hex[:8]}"

        print(f"🧪 Starting Test for: {fake_course_id} / {fake_module_id}")

        # 2. Upload Video
        blob_path = f"videos/{fake_course_id}/{fake_module_id}_{file.filename}"
        blob_client = blob_service_client.get_blob_client(
            container=settings.BLOB_CONTAINER_NAME,
            blob=blob_path
        )

        file_content = await file.read()
        blob_client.upload_blob(file_content, overwrite=True)
        print(f"✅ Video Uploaded to: {blob_path}")

        # 3. Generate SAS (Critical for Azure Speech to access the file)
        video_sas_url = generate_test_sas(blob_path)
        if not video_sas_url:
            raise HTTPException(status_code=500, detail="Failed to generate SAS token")

        # 4. Trigger the AI Pipeline
        background_tasks.add_task(
            run_ai_pipeline,
            video_sas_url,
            fake_course_id,
            fake_module_id,
            file.filename
        )

        return {
            "message": "Test Upload Successful. AI Pipeline Started.",
            "debug_info": {
                "course_id": fake_course_id,
                "module_id": fake_module_id,
                "firestore_path": f"ai_assets/{fake_module_id}",
                "transcript_location": f"transcripts/{fake_course_id}/{fake_module_id}.txt"
            }
        }

    except Exception as e:
        print(f"Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

















































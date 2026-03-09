"""
Storage operations - Azure Blob Storage integration
"""
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from datetime import datetime, timedelta
from typing import Optional

from core.database import db
from core.security import get_current_user
from core.responses import format_success
from core.exceptions import (
    StorageException,
    NotFoundException,
    ValidationException,
    LMSException
)
from storage.services import (
    generate_upload_sas,
    generate_download_sas,
    verify_file_upload
)

router = APIRouter()


@router.post("/upload")
async def generate_upload_url(
        file_name: str = Form(...),
        file_size: int = Form(...),
        file_type: str = Form(default="video/mp4"),
        user: dict = Depends(get_current_user)
):
    """
    Generate a temporary SAS URL for client-side direct upload to Azure Blob.

    This prevents large files from being uploaded through FastAPI,
    instead using Azure's direct upload mechanism.

    Args:
        file_name: Name of the file to upload
        file_size: Size of the file in bytes
        file_type: MIME type of the file
        user: Authenticated user context

    Returns:
        SAS URL with 1-hour expiry for direct upload
    """
    try:
        # ========== VALIDATION ==========
        MAX_FILE_SIZE = 10 * 1024 * 1024 * 1024  # 10GB

        if file_size > MAX_FILE_SIZE:
            raise ValidationException(
                f"File size {file_size} exceeds maximum {MAX_FILE_SIZE} bytes",
                details={"max_size": MAX_FILE_SIZE}
            )

        if not file_name or not file_name.strip():
            raise ValidationException("File name cannot be empty")

        # Validate file type
        allowed_types = ["video/mp4", "video/quicktime", "video/x-msvideo"]
        if file_type not in allowed_types:
            raise ValidationException(
                f"File type {file_type} not allowed",
                details={"allowed_types": allowed_types}
            )

        # ========== GENERATE SAS URL ==========
        instructor_id = user['uid']
        timestamp = int(datetime.now().timestamp())
        blob_path = f"uploads/{instructor_id}/{timestamp}_{file_name}"

        sas_url = generate_upload_sas(
            blob_path=blob_path,
            expiry_hours=1  # 1-hour expiry
        )

        if not sas_url:
            raise StorageException("Failed to generate upload URL")

        # ========== SAVE UPLOAD RECORD ==========
        # Store pending upload info in Firestore for tracking
        upload_record = {
            "file_name": file_name,
            "file_size": file_size,
            "file_type": file_type,
            "instructor_id": instructor_id,
            "blob_path": blob_path,
            "status": "pending",  # Will become "completed" after upload
            "created_at": datetime.utcnow().isoformat(),
            "expires_at": (datetime.utcnow() + timedelta(hours=1)).isoformat()
        }

        upload_ref = db.collection("uploads").document()
        upload_ref.set(upload_record)

        return format_success(
            message="Upload URL generated successfully",
            data={
                "sas_url": sas_url,
                "blob_path": blob_path,
                "upload_id": upload_ref.id,
                "expires_in_seconds": 3600,
                "instructions": "Use this SAS URL to upload directly to Azure Blob Storage"
            }
        )

    except LMSException:
        raise
    except Exception as e:
        raise StorageException(f"Upload URL generation failed: {str(e)}")


@router.post("/upload/confirm/{upload_id}")
async def confirm_upload(
        upload_id: str,
        title: str = Form(...),
        user: dict = Depends(get_current_user)
):
    """
    Confirm that a file has been uploaded to Azure.
    This creates a video record in Firestore and triggers AI pipeline.

    Args:
        upload_id: ID of the upload record
        title: Video title
        user: Authenticated user context
    """
    try:
        # ========== VALIDATION ==========
        if not upload_id or not upload_id.strip():
            raise ValidationException("Upload ID is required")

        if not title or not title.strip():
            raise ValidationException("Title cannot be empty")

        # ========== FETCH UPLOAD RECORD ==========
        upload_ref = db.collection("uploads").document(upload_id)
        upload_doc = upload_ref.get()

        if not upload_doc.exists:
            raise NotFoundException(upload_id, "Upload")

        upload_data = upload_doc.to_dict()

        # Verify ownership
        if upload_data.get("instructor_id") != user['uid']:
            raise LMSException(
                "Unauthorized: This upload does not belong to you",
                "AUTH_003",
                status_code=403
            )

        # ========== CREATE VIDEO RECORD ==========
        from courses.services import generate_read_sas
        from ai_features.services import run_ai_pipeline
        from fastapi import BackgroundTasks

        # Generate read SAS for the uploaded file
        read_sas_url = generate_read_sas(upload_data["blob_path"])

        # Create video document
        video_ref = db.collection("videos").document()
        video_ref.set({
            "title": title,
            "instructor_id": user['uid'],
            "upload_id": upload_id,
            "video_url": read_sas_url,
            "storage_path": upload_data["blob_path"],
            "filename": upload_data["file_name"],
            "status": "processing",
            "created_at": datetime.utcnow().isoformat(),
            "summary": "AI is analyzing this video...",
            "transcript": ""
        })

        # ========== TRIGGER AI PIPELINE (Asynchronous) ==========
        # Note: In production, use Celery or similar for true async
        from fastapi import BackgroundTasks
        background_tasks = BackgroundTasks()
        background_tasks.add_task(
            run_ai_pipeline,
            video_ref.id,
            read_sas_url,
            upload_data["file_name"]
        )

        # Update upload record status
        upload_ref.update({"status": "completed", "video_id": video_ref.id})

        return format_success(
            message="Video uploaded and processing started",
            data={
                "video_id": video_ref.id,
                "status": "processing"
            }
        )

    except LMSException:
        raise
    except Exception as e:
        raise StorageException(f"Upload confirmation failed: {str(e)}")
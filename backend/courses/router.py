#
#
# from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Depends, BackgroundTasks
# from datetime import datetime
# from firebase_admin import firestore
#
# # Imports from Core
# from core.database import db
# from core.security import get_current_user
# from courses.services import upload_blob, generate_read_sas
#
# # Import the AI Pipeline function
# from ai_features.services import run_ai_pipeline
#
# router = APIRouter()
#
# @router.post("/upload")
# async def upload_video(
#     background_tasks: BackgroundTasks,  # <--- INJECT BACKGROUND TASKS
#     file: UploadFile = File(...),
#     title: str = Form(...),
#     user: dict = Depends(get_current_user)
# ):
#     try:
#         instructor_id = user['uid']
#         clean_filename = file.filename.replace(" ", "_")
#         timestamp = int(datetime.now().timestamp())
#
#         # Path structure: instructors/{uid}/videos/...
#         blob_path = f"instructors/{instructor_id}/videos/{timestamp}_{clean_filename}"
#
#         # 1. Upload to Azure
#         file_content = await file.read()
#         upload_blob(file_content, blob_path)
#
#         # 2. Generate Link (Needed for Frontend AND for AI to download it)
#         sas_url = generate_read_sas(blob_path)
#
#         # 3. Save to Firebase (Old Schema)
#         doc_ref = db.collection("videos").document()
#         doc_ref.set({
#             "title": title,
#             "instructor_id": instructor_id,
#             "video_url": sas_url,
#             "storage_path": blob_path,
#             "filename": clean_filename,
#             "status": "processing", # <--- Set status to processing immediately
#             "created_at": firestore.SERVER_TIMESTAMP,
#             "summary": "AI is analyzing this video...", # Placeholder
#             "transcript": ""
#         })
#
#         # 4. TRIGGER AI AUTOMATICALLY 🚀
#         # We pass the doc_id, the SAS URL, and the filename to the AI worker
#         background_tasks.add_task(run_ai_pipeline, doc_ref.id, sas_url, clean_filename)
#
#         return {
#             "message": "Upload successful. AI processing started automatically.",
#             "video_id": doc_ref.id
#         }
#
#     except Exception as e:
#         print(f"❌ Upload Error: {e}")
#         raise HTTPException(status_code=500, detail=str(e))
#
# @router.get("/")
# def get_videos(user: dict = Depends(get_current_user)):
#     """
#     Fetches videos using the Old Schema logic
#     """
#     docs = db.collection("videos").order_by("created_at", direction=firestore.Query.DESCENDING).stream()
#     videos = []
#     for doc in docs:
#         data = doc.to_dict()
#         if "created_at" in data and data["created_at"] is not None:
#             data["created_at"] = data["created_at"].isoformat()
#         data["id"] = doc.id
#         videos.append(data)
#     return videos


from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Depends, BackgroundTasks
from datetime import datetime
from firebase_admin import firestore
import uuid
from google.cloud.firestore_v1.base_query import FieldFilter
from google.cloud.firestore_v1 import ArrayUnion


# Imports from Core
from core.database import db
from core.security import get_current_user
from courses.services import upload_blob, generate_read_sas

# Import the AI Pipeline function
from ai_features.services import run_ai_pipeline

router = APIRouter()


@router.post("/")
async def create_course(
        title: str = Form(...),
        category: str = Form("GenAi"),  # 🆕 Added Category
        user: dict = Depends(get_current_user)
):
    """Creates a new top-level course."""
    try:
        instructor_id = user['uid']
        doc_ref = db.collection("courses").document()

        course_data = {
            "id": doc_ref.id,
            "title": title,
            "category": category,  # 🆕 Save to Firestore
            "instructor_id": instructor_id,
            "is_published": False,
            "created_at": firestore.SERVER_TIMESTAMP
        }

        doc_ref.set(course_data)

        return {"message": "Course created successfully", "course_id": doc_ref.id}
    except Exception as e:
        print(f"❌ Error creating course: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/my-courses")
async def get_my_courses(user: dict = Depends(get_current_user)):
    """Fetches courses created by this specific instructor."""
    try:
        instructor_id = user['uid']

        # FIXED: Using FieldFilter to remove the UserWarning
        docs = db.collection("courses") \
            .where(filter=FieldFilter("instructor_id", "==", instructor_id)) \
            .order_by("created_at", direction=firestore.Query.DESCENDING) \
            .stream()

        courses = []
        for doc in docs:
            data = doc.to_dict()
            if "created_at" in data and data["created_at"] is not None:
                data["created_at"] = data["created_at"].isoformat()
            courses.append(data)

        return courses
    except Exception as e:
        print(f"❌ Error fetching courses: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{course_id}/modules")
async def upload_module(
        course_id: str,
        background_tasks: BackgroundTasks,
        title: str = Form(...),
        file: UploadFile = File(...),
        user: dict = Depends(get_current_user)
):
    """Uploads a video as a module inside a course and triggers AI."""
    try:
        clean_filename = file.filename.replace(" ", "_")
        module_id = f"mod_{uuid.uuid4().hex[:8]}"

        print(f"📦 Uploading Module: {module_id} for Course: {course_id}")

        # 1. Structure Blob Path: videos/{course_id}/{module_id}_{filename}
        blob_path = f"videos/{course_id}/{module_id}_{clean_filename}"

        # 2. Upload to Azure (using your existing services.py logic)
        file_content = await file.read()
        upload_blob(file_content, blob_path)

        # 3. Generate SAS (Needed for Frontend AND for AI to download it)
        sas_url = generate_read_sas(blob_path)
        if not sas_url:
            raise HTTPException(status_code=500, detail="Failed to generate SAS token")

        # 4. Save Module to Firestore Subcollection
        # Path: courses/{course_id}/modules/{module_id}
        module_ref = db.collection("courses").document(course_id).collection("modules").document(module_id)

        # Count existing modules to assign an order_index
        existing_modules = db.collection("courses").document(course_id).collection("modules").get()
        order_index = len(existing_modules)

        module_ref.set({
            "id": module_id,
            "title": title,
            "video_blob_url": sas_url,
            "order_index": order_index,
            "status": "processing",  # Instructor UI will show this status
            "created_at": firestore.SERVER_TIMESTAMP
        })

        # 5. TRIGGER AI PIPELINE 🚀
        # Notice we pass module_id twice (once for the ai_assets doc ID, once for internal logic)
        background_tasks.add_task(
            run_ai_pipeline,
            sas_url,
            course_id,
            module_id,
            clean_filename
        )

        return {
            "message": "Module uploaded successfully. AI processing started.",
            "module_id": module_id
        }

    except Exception as e:
        print(f"❌ Upload Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

#STUDENT

@router.get("/catalog")
async def get_course_catalog(user: dict = Depends(get_current_user)):
    """Fetches all courses available for students to enroll in."""
    try:
        # For now, return all courses. In a real app, you'd filter by 'is_published'
        docs = db.collection("courses").order_by("created_at", direction=firestore.Query.DESCENDING).stream()
        return[{"id": doc.id, **doc.to_dict()} for doc in docs]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{course_id}/enroll")
async def enroll_in_course(course_id: str, user: dict = Depends(get_current_user)):
    """Enrolls a student in a course by updating their user document."""
    try:
        user_ref = db.collection("users").document(user['uid'])
        # Add course to enrollments map with an empty completed_modules array
        user_ref.set({
            "enrollments": {
                course_id: {
                    "enrolled_at": firestore.SERVER_TIMESTAMP,
                    "completed_modules":[]
                }
            }
        }, merge=True)
        return {"message": "Successfully enrolled!"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{course_id}/modules")
async def get_course_modules(course_id: str, user: dict = Depends(get_current_user)):
    """Fetches all modules for a specific course, ordered by order_index."""
    try:
        docs = db.collection("courses").document(course_id).collection("modules").order_by("order_index").stream()
        return [doc.to_dict() for doc in docs]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{course_id}/modules/{module_id}/complete")
async def complete_module(course_id: str, module_id: str, user: dict = Depends(get_current_user)):
    """Marks a module as completed in the student's enrollment data (Unlocks the next one)."""
    try:
        user_ref = db.collection("users").document(user['uid'])
        # Atomically add the module_id to the completed_modules array
        user_ref.update({
            f"enrollments.{course_id}.completed_modules": ArrayUnion([module_id])
        })
        return {"message": "Module completed successfully!"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/my-profile")
async def get_student_profile(user: dict = Depends(get_current_user)):
    """Fetches the student's profile, including their enrollments."""
    try:
        doc = db.collection("users").document(user['uid']).get()
        if not doc.exists:
            raise HTTPException(status_code=404, detail="User profile not found")
        return doc.to_dict()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{course_id}")
async def delete_course(course_id: str, user: dict = Depends(get_current_user)):
    """Deletes a course."""
    try:
        # Note: In a production app, you'd also delete subcollections and blobs.
        db.collection("courses").document(course_id).delete()
        return {"message": "Course deleted successfully."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{course_id}/modules/{module_id}")
async def delete_module(course_id: str, module_id: str, user: dict = Depends(get_current_user)):
    """Deletes a specific module."""
    try:
        db.collection("courses").document(course_id).collection("modules").document(module_id).delete()
        return {"message": "Module deleted successfully."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{course_id}/modules/{module_id}")
async def edit_module(
        course_id: str,
        module_id: str,
        background_tasks: BackgroundTasks,
        title: str = Form(None),
        file: UploadFile = File(None),
        user: dict = Depends(get_current_user)
):
    """Updates a module's title and/or replaces the video (re-triggers AI)."""
    try:
        update_data = {}
        if title:
            update_data["title"] = title

        # If a new file is uploaded, replace it in Blob Storage and re-run AI
        if file:
            clean_filename = file.filename.replace(" ", "_")
            blob_path = f"videos/{course_id}/{module_id}_{clean_filename}"

            file_content = await file.read()
            upload_blob(file_content, blob_path)
            sas_url = generate_read_sas(blob_path)

            if sas_url:
                update_data["video_blob_url"] = sas_url
                update_data["status"] = "processing"  # Reset status for UI

                # Re-trigger AI pipeline
                background_tasks.add_task(run_ai_pipeline, sas_url, course_id, module_id, clean_filename)

        # Update Firestore Document
        if update_data:
            db.collection("courses").document(course_id).collection("modules").document(module_id).update(update_data)

        return {"message": "Module updated successfully!"}
    except Exception as e:
        print(f"❌ Error updating module: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{course_id}/analytics")
async def get_course_analytics(course_id: str, user: dict = Depends(get_current_user)):
    """Fetches analytics (enrolled students and progress) for a specific course."""
    try:
        # 1. Get total modules for this course
        modules_ref = db.collection("courses").document(course_id).collection("modules").get()
        total_modules = len(modules_ref)

        # 2. Fetch all students
        users_ref = db.collection("users").where(filter=FieldFilter("role", "==", "student")).stream()

        analytics = []
        for u in users_ref:
            user_data = u.to_dict()
            enrollments = user_data.get("enrollments", {})

            # 3. Check if this student is enrolled in THIS course
            if course_id in enrollments:
                course_data = enrollments[course_id]
                completed_modules = len(course_data.get("completed_modules", []))
                progress = int((completed_modules / total_modules * 100)) if total_modules > 0 else 0

                analytics.append({
                    "email": user_data.get("email"),
                    "completed_modules": completed_modules,
                    "progress": progress
                })

        return {"total_modules": total_modules, "students": analytics}
    except Exception as e:
        print(f"Error fetching analytics: {e}")
        raise HTTPException(status_code=500, detail=str(e))
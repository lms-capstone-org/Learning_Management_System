from fastapi import APIRouter, Depends, HTTPException, status
from google.cloud.firestore_v1 import transactional
from google.cloud.firestore_v1.base_query import FieldFilter
from core.database import db
from core.security import get_current_user, require_student
from users.schemas import UserResponse, UpdateProfileRequest
from users.services import UserService

router = APIRouter()
core_router = APIRouter()  # Secondary router for the /core prefix — avoids merge conflicts with Developer 3


# ==========================================
# Existing Endpoints (Preserved)
# ==========================================
@router.post("/sync")
def sync_user(user: dict = Depends(get_current_user)):
    profile = UserService.ensure_user_exists(user["uid"], user["email"])
    return profile

@router.get("/me", response_model=UserResponse)
def get_my_profile(user: dict = Depends(get_current_user)):
    """Returns user profile including role — frontend uses this instead of reading Firestore directly."""
    profile = UserService.get_profile(user["uid"])
    if not profile:
        raise HTTPException(status_code=404, detail="User profile not found")
    return profile

@router.patch("/me")
def update_my_profile(
    body: UpdateProfileRequest,
    user: dict = Depends(get_current_user)
):
    updates = body.model_dump(exclude_none=True)
    if not updates:
        raise HTTPException(status_code=400, detail="Nothing to update")
    return UserService.update_profile(user["uid"], updates)


# ==========================================
# Developer 2: Module Completion Endpoint
# ==========================================
# Mounted on core_router (no prefix) so the final URL is:
#   POST /core/courses/{course_id}/modules/{module_id}/complete
# This matches the frontend API contract from the Master Architecture.

@core_router.post("/core/courses/{course_id}/modules/{module_id}/complete")
def complete_module(
    course_id: str,
    module_id: str,
    current_user: dict = Depends(require_student)
):
    """
    Marks a module as completed for the authenticated student.
    Uses a Firestore Transaction to atomically append the module_id
    to the user's completed_modules array, preventing race conditions
    during rapid clicks.
    """
    uid = current_user["uid"]
    user_ref = db.collection("users").document(uid)

    @transactional
    def update_completed_modules_in_transaction(transaction, ref):
        snapshot = ref.get(transaction=transaction)
        if not snapshot.exists:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"status": "error", "message": "User not found", "code": "NOT_FOUND_404"}
            )

        user_data = snapshot.to_dict()
        enrollments = user_data.get("enrollments", {})

        if course_id not in enrollments:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"status": "error", "message": "User not enrolled in this course", "code": "BAD_REQUEST_400"}
            )

        course_enrollment = enrollments[course_id]
        completed_modules = course_enrollment.get("completed_modules", [])

        if module_id not in completed_modules:
            completed_modules.append(module_id)
            # Atomically update the nested field and last_accessed timestamp
            from google.cloud.firestore_v1 import SERVER_TIMESTAMP
            transaction.update(ref, {
                f"enrollments.{course_id}.completed_modules": completed_modules,
                f"enrollments.{course_id}.last_accessed": SERVER_TIMESTAMP
            })

        return completed_modules

    transaction = db.transaction()
    try:
        updated_modules = update_completed_modules_in_transaction(transaction, user_ref)
        return {"status": "success", "completed_modules": updated_modules}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"status": "error", "message": str(e), "code": "INTERNAL_ERROR_500"}
        )
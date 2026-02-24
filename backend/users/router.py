from fastapi import APIRouter, Depends, HTTPException
from core.security import get_current_user
from users.schemas import UserResponse, UpdateProfileRequest
from users.services import UserService

router = APIRouter()

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
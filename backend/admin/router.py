from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Optional
from core.security import require_admin
from admin.schemas import AssignRoleRequest, UserListResponse
from admin.services import AdminService, VALID_ROLES

router = APIRouter()

@router.post("/assign-role")
def assign_role(
    request: AssignRoleRequest,
    admin: dict = Depends(require_admin)
):
    if request.role not in VALID_ROLES:
        raise HTTPException(
            status_code=400, 
            detail=f"Invalid role. Must be one of {VALID_ROLES}"
        )
    try:
        result = AdminService.assign_role(request.uid, request.role)
        return {"message": "Role updated successfully", **result}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/users", response_model=UserListResponse)
def list_users(
    limit: int = Query(default=20, ge=1, le=100),  # max 100 per page
    cursor: Optional[str] = None,
    role: Optional[str] = None,
    search: Optional[str] = None,
    admin: dict = Depends(require_admin)
):
    return AdminService.list_users(limit, cursor, role, search)


@router.get("/user/{uid}")
def get_user(uid: str, admin: dict = Depends(require_admin)):
    user = AdminService.get_user(uid)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user
from pydantic import BaseModel
from typing import Optional

class AssignRoleRequest(BaseModel):
    uid: str
    role: str

class AdminUserResponse(BaseModel):
    uid: str
    email: Optional[str] = None
    role: Optional[str] = None

class UserListResponse(BaseModel):
    users: list[AdminUserResponse]
    next_cursor: Optional[str] = None
    limit: int
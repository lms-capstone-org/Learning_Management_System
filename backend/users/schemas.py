from pydantic import BaseModel
from typing import Optional

class UserResponse(BaseModel):
    uid: str
    email: Optional[str] = None
    full_name: Optional[str] = None
    role: str

class UpdateProfileRequest(BaseModel):
    full_name: Optional[str] = None
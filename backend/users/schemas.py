from pydantic import BaseModel, EmailStr
from typing import Optional, Dict, List
from datetime import datetime

# --- New Models (Developer 2: Firestore-aligned) ---
class Enrollment(BaseModel):
    enrolled_at: datetime
    last_accessed: datetime
    completed_modules: List[str] = []

class UserInDB(BaseModel):
    uid: str
    email: EmailStr
    role: str
    created_at: datetime
    enrollments: Optional[Dict[str, Enrollment]] = {}

# --- Existing Models (Preserved from Developer 1) ---
class UserResponse(BaseModel):
    uid: str
    email: Optional[str] = None
    full_name: Optional[str] = None
    role: str

class UpdateProfileRequest(BaseModel):
    full_name: Optional[str] = None
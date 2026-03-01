from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class CourseCreate(BaseModel):
    title: str
    description: Optional[str] = None

class CourseInDB(CourseCreate):
    id: str
    instructor_id: str
    is_published: bool = False
    created_at: datetime

class ModuleCreate(BaseModel):
    title: str
    video_url: str
    order_index: int

class ModuleInDB(BaseModel):
    id: str
    title: str
    video_blob_url: str
    order_index: int
    has_summary: bool = False
    has_quiz: bool = False
    is_vectorized: bool = False

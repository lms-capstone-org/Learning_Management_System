from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from core.database import db # Initializes DB on startup

# Import Routers
from courses.router import router as courses_router
from ai_features.router import router as ai_router

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount Routers
# /courses/upload, /courses/videos
app.include_router(courses_router, prefix="/courses", tags=["Courses"])

# /ai/process-video/{id}
app.include_router(ai_router, prefix="/ai", tags=["AI Features"])

@app.get("/")
def health_check():
    return {"status": "LMS Backend is Running"}
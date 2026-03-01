from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from core.database import db
from courses.router import router as courses_router
from ai_features.router import router as ai_router
from admin.router import router as admin_router   # added this
from users.router import router as users_router
from users.router import core_router              # line 8
app.include_router(core_router, tags=["Core Processing"])  #core_router mount

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # tightened this from *
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(courses_router, prefix="/courses", tags=["Courses"])
app.include_router(ai_router, prefix="/ai", tags=["AI Features"])
app.include_router(admin_router, prefix="/admin", tags=["Admin"])  # added this
app.include_router(users_router, prefix="/users", tags=["Users"])

@app.get("/")
def health_check():
    return {"status": "LMS Backend is Running"}
#
#
# # backend/test_ai_main.py
# from fastapi import FastAPI
# from fastapi.middleware.cors import CORSMiddleware
#
# # 1. Import ONLY your router
# from ai_features.router import router as ai_router
#
# app = FastAPI(title="AI Features Sandbox")
#
# # 2. Add CORS (so your React frontend can talk to it)
# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=["*"],
#     allow_methods=["*"],
#     allow_headers=["*"],
# )
#
# # 3. Mount ONLY your router
# app.include_router(ai_router, prefix="/ai", tags=["AI Features"])
#
# @app.get("/")
# def health_check():
#     return {"status": "AI Sandbox is Running 🚀"}

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

# Import the router from ai_features
from ai_features.router import router as ai_router

app = FastAPI(title="AI Features Sandbox")

# Allow CORS so your Frontend can access the stream
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include the router
app.include_router(ai_router, prefix="/ai", tags=["AI Features"])

@app.get("/")
def health_check():
    return {"status": "AI System Operational 🚀"}

if __name__ == "__main__":
    uvicorn.run("test_ai_main:app", host="0.0.0.0", port=8000, reload=True)
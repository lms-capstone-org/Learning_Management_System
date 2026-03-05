from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from datetime import datetime
import traceback

# Import your modules
from core.database import db
from core.exceptions import LMSException, ErrorCode
from core.responses import format_error
from courses.router import router as courses_router
from ai_features.router import router as ai_router
from storage.router import router as storage_router

app = FastAPI(
    title="LTC AI LMS",
    description="Learning Management System with AI-powered video analysis",
    version="1.0.0"
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # TODO: Change in production
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============ GLOBAL EXCEPTION HANDLERS ============

@app.exception_handler(LMSException)
async def lms_exception_handler(request: Request, exc: LMSException):
    """Handle custom LMS exceptions"""
    return JSONResponse(
        status_code=exc.status_code,
        content=format_error(
            message=exc.message,
            code=exc.code.value,
            path=str(request.url.path),
            details=exc.details
        )
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle Pydantic validation errors"""
    errors = []
    for error in exc.errors():
        errors.append({
            "field": ".".join(str(x) for x in error["loc"][1:]),
            "message": error["msg"],
            "type": error["type"]
        })

    return JSONResponse(
        status_code=422,
        content=format_error(
            message="Validation error",
            code=ErrorCode.INVALID_INPUT.value,
            path=str(request.url.path),
            details={"errors": errors}
        )
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Catch all unhandled exceptions"""
    print(f"❌ UNHANDLED EXCEPTION: {str(exc)}")
    traceback.print_exc()

    return JSONResponse(
        status_code=500,
        content=format_error(
            message="Internal server error",
            code=ErrorCode.SERVER_ERROR.value,
            path=str(request.url.path),
            details={"error": str(exc)} if app.debug else None
        )
    )


# ============ ROUTERS ============

app.include_router(courses_router, prefix="/courses", tags=["Courses"])
app.include_router(ai_router, prefix="/ai", tags=["AI Features"])
app.include_router(storage_router, prefix="/core", tags=["Core"])


# ============ HEALTH CHECK ============

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    from core.responses import format_success
    return format_success(
        message="LMS Backend is healthy",
        data={"status": "running"}
    )


@app.get("/")
async def root():
    """Root endpoint"""
    from core.responses import format_success
    return format_success(
        message="Welcome to LTC AI LMS",
        data={
            "version": "1.0.0",
            "docs": "/docs"
        }
    )
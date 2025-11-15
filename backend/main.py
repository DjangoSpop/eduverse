"""
Eduverse API - Main Application Entry Point

AI-powered interactive learning platform backend.
Transforms curriculum PDFs into 3D learning experiences for children.
"""

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from contextlib import asynccontextmanager
import time
import uvicorn

from app.core.config import settings
from app.core.logging import setup_logging, get_logger
from app.api.endpoints import curriculum, lessons, sessions, learners, multilingual, streaming
from app.storage import memory_store


# Setup logging
setup_logging(settings.log_level)
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager.

    Handles startup and shutdown events.
    """
    # Startup
    logger.info(f"Starting {settings.api_title} v{settings.api_version}")
    logger.info(f"Environment: {settings.environment}")
    logger.info(f"Log level: {settings.log_level}")
    logger.info(f"Allowed origins: {settings.allowed_origins}")

    yield

    # Shutdown
    logger.info("Shutting down Eduverse API")


# Create FastAPI application
app = FastAPI(
    title=settings.api_title,
    version=settings.api_version,
    description=settings.api_description,
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)


# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Request timing middleware
@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    """Add processing time to response headers"""
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    return response


# Exception handlers
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle validation errors with detailed messages"""
    logger.warning(f"Validation error on {request.url.path}: {exc.errors()}")

    return JSONResponse(
        status_code=422,
        content={
            "detail": "Validation error",
            "errors": exc.errors(),
            "body": str(exc.body) if exc.body else None
        }
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle unexpected errors"""
    logger.error(f"Unexpected error on {request.url.path}: {str(exc)}", exc_info=True)

    return JSONResponse(
        status_code=500,
        content={
            "detail": "Internal server error",
            "message": str(exc) if settings.environment == "development" else "An error occurred"
        }
    )


# Include routers
app.include_router(curriculum.router, prefix="/api")
app.include_router(lessons.router, prefix="/api")
app.include_router(sessions.router, prefix="/api")
app.include_router(learners.router, prefix="/api")
app.include_router(multilingual.router, prefix="/api")  # Sprint 5: Multilingual support
app.include_router(streaming.router, prefix="/api")  # Sprint 5: Real-time streaming


# Root endpoints
@app.get("/")
async def root():
    """
    API information and health check.

    Returns overview of available endpoints and system status.
    """
    return {
        "service": settings.api_title,
        "version": settings.api_version,
        "description": settings.api_description,
        "status": "operational",
        "environment": settings.environment,
        "documentation": {
            "swagger": "/docs",
            "redoc": "/redoc",
            "openapi": "/openapi.json"
        },
        "endpoints": {
            "curriculum": "/api/curriculum",
            "lessons": "/api/lessons",
            "sessions": "/api/sessions",
            "learners": "/api/learners",
            "multilingual": "/api/multilingual",
            "streaming": "/api/streaming"
        },
        "features": {
            "multilingual_support": True,
            "supported_languages": ["ar", "en", "fr", "es", "zh", "he", "ur"],
            "rtl_support": True,
            "cultural_adaptation": True,
            "realtime_streaming": True,
            "dynamic_content_generation": True,
            "behavior_based_adaptation": True
        }
    }


@app.get("/health")
async def health():
    """
    Health check endpoint.

    Used by monitoring systems to verify service is running.
    """
    stats = memory_store.get_storage_stats()

    return {
        "status": "healthy",
        "version": settings.api_version,
        "environment": settings.environment,
        "storage": stats
    }


@app.get("/api/stats")
async def get_stats():
    """
    Get system statistics.

    Returns current storage usage and counts.
    """
    stats = memory_store.get_storage_stats()

    return {
        "storage": stats,
        "endpoints": {
            "curriculum": stats["curriculum_count"],
            "lessons": stats["lesson_count"],
            "learners": stats["learner_count"],
            "sessions": stats["session_count"]
        }
    }


# Development utilities
if settings.environment == "development":
    @app.post("/api/dev/reset-storage")
    async def reset_storage():
        """
        Reset all storage (development only).

        WARNING: This deletes all data!
        """
        logger.warning("RESETTING ALL STORAGE - Development mode")
        memory_store.MemoryStore.clear_all_stores()

        return {
            "message": "All storage cleared",
            "warning": "All data has been deleted"
        }


# Main entry point
if __name__ == "__main__":
    print(f"""
╔══════════════════════════════════════════════════════════════╗
║                  EDUVERSE API SERVER                         ║
║      AI-Powered Interactive Learning Platform                ║
║                                                              ║
║  Version: {settings.api_version:<48} ║
║  Environment: {settings.environment:<44} ║
║                                                              ║
║  Starting server...                                          ║
╚══════════════════════════════════════════════════════════════╝

Server URL: http://{settings.api_host}:{settings.api_port}
API Documentation: http://{settings.api_host}:{settings.api_port}/docs
Interactive Docs: http://{settings.api_host}:{settings.api_port}/redoc

Available Endpoints:
  - POST   /api/curriculum/upload      Upload curriculum PDF
  - POST   /api/curriculum/analyze     Analyze curriculum with AI
  - POST   /api/lessons/generate       Generate interactive lesson
  - GET    /api/lessons/{{lesson_id}}   Retrieve lesson for Unity
  - POST   /api/sessions/start         Start learning session
  - POST   /api/learners/              Create learner profile

Press CTRL+C to stop the server
""")

    uvicorn.run(
        "main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.api_reload,
        log_level=settings.log_level.lower()
    )

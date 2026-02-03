"""AI Image Hub - Main FastAPI Application"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import router
from app.core.config import get_settings
from app.core.database import init_db

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events"""
    # Startup
    await init_db()
    yield
    # Shutdown (cleanup if needed)


app = FastAPI(
    title="AI Image Hub",
    description="""
    AI Image Hub - Automated image generation and editing platform.

    This API integrates ChatGPT for intelligent prompt generation and
    Nanobanano Pro for high-quality image generation and editing.

    ## Features

    - **Generate Images**: Create new images from text descriptions in any language
    - **Edit Images**: Modify existing images with AI-powered editing
    - **Transaction History**: Full logging of all operations

    ## Authentication

    All endpoints (except /health) require the `X-API-Token` header.
    """,
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(router, prefix="/api/v1", tags=["Image Generation"])


@app.get("/", tags=["Root"])
async def root():
    """Root endpoint with API info"""
    return {
        "name": "AI Image Hub",
        "version": "1.0.0",
        "description": "ChatGPT + Nanobanano Integration for AI Image Generation",
        "docs": "/docs",
        "health": "/api/v1/health",
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
    )

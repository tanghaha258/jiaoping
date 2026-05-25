"""FastAPI application entry point for 智跨学评."""

import os
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from app.core.config import settings
from app.core.exceptions import AppException
from app.core.response import error_response
from app.api.v1.router import api_router
from app.db.session import AsyncSessionFactory, engine
from app.db.base import Base
from app.db.seed import seed_database


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifecycle: create tables on startup, seed if needed."""
    # Ensure upload directory exists
    os.makedirs(os.path.abspath(settings.UPLOAD_DIR), exist_ok=True)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with AsyncSessionFactory() as session:
        await seed_database(session)
        await session.commit()

    yield
    await engine.dispose()


app = FastAPI(
    title="智跨学评 API",
    description="AI-powered junior high school interdisciplinary teaching-assessment integration platform",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(AppException)
async def app_exception_handler(request: Request, exc: AppException) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content=error_response(
            code=exc.code,
            message=exc.message,
            status_code=exc.status_code,
        ),
    )


app.include_router(api_router, prefix="/api/v1")

# Mount uploads directory for static file serving
uploads_dir = os.path.abspath(settings.UPLOAD_DIR)
if not os.path.exists(uploads_dir):
    os.makedirs(uploads_dir, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=uploads_dir), name="uploads")

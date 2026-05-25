"""Health check endpoint."""

from fastapi import APIRouter

from app.core.response import success_response

router = APIRouter()


@router.get("/health")
async def health_check():
    """Return service health status."""
    return success_response(
        data={
            "status": "ok",
            "version": "0.1.0",
        },
        message="Service is healthy",
    )

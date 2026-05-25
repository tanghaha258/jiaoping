"""Standard API response helpers."""

import uuid
from typing import Any, Optional


def generate_trace_id() -> str:
    """Generate a unique trace ID for request tracking."""
    return f"req_{uuid.uuid4().hex[:12]}"


def success_response(data: Any = None, message: str = "success") -> dict:
    """Create a standard success response."""
    return {
        "code": 0,
        "message": message,
        "data": data,
        "trace_id": generate_trace_id(),
    }


def error_response(code: int, message: str, status_code: int = 400) -> dict:
    """Create a standard error response."""
    return {
        "code": code,
        "message": message,
        "data": None,
        "trace_id": generate_trace_id(),
    }


def paginated_response(items: list, total: int, page: int, page_size: int) -> dict:
    """Create a paginated response."""
    return success_response(data={
        "items": items,
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": (total + page_size - 1) // page_size if page_size > 0 else 0,
    })

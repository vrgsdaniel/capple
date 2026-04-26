from datetime import UTC, datetime

from fastapi import HTTPException


def timestamp() -> str:
    """Return the current UTC timestamp in ISO-8601 format."""
    return datetime.now(tz=UTC).isoformat()


def http_error_response(error_message: str, error_code: int) -> HTTPException:
    """Build a structured HTTPException to be raised by route handlers."""
    return HTTPException(status_code=error_code, detail=error_message)

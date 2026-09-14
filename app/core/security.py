"""
Service-to-service authentication.

.NET calls this API with a static API key in a header. This is not a user
auth system; there is no login flow here.
"""
from fastapi import Header, HTTPException, status

from app.core.config import get_settings
from app.core.errors import AppError


async def verify_api_key(x_api_key: str = Header(default="")) -> None:
    settings = get_settings()
    if not x_api_key or x_api_key != settings.API_KEY:
        raise AppError(
            code="UNAUTHORIZED",
            message="Missing or invalid API key.",
            status_code=status.HTTP_401_UNAUTHORIZED,
        )

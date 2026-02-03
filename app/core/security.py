"""Security utilities for API authentication"""

from fastapi import HTTPException, Security, status
from fastapi.security import APIKeyHeader

from app.core.config import get_settings

api_key_header = APIKeyHeader(name="X-API-Token", auto_error=False)


async def verify_api_token(api_key: str = Security(api_key_header)) -> str:
    """
    Verify the API token from request header.

    Args:
        api_key: Token from X-API-Token header

    Returns:
        The validated API key

    Raises:
        HTTPException: If token is missing or invalid
    """
    settings = get_settings()

    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API token is missing. Provide X-API-Token header."
        )

    if api_key != settings.api_secret_token:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid API token"
        )

    return api_key

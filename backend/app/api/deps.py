"""
API dependency injection.

Common dependencies used across API endpoints.
"""

from typing import Optional
from fastapi import Header, HTTPException, status


async def verify_api_key(x_api_key: Optional[str] = Header(None)) -> str:
    """
    Verify API key (if authentication is enabled).

    For MVP, this is a placeholder. In production, this would
    validate API keys from a database.

    Args:
        x_api_key: API key from header

    Returns:
        str: Validated API key

    Raises:
        HTTPException: If API key is invalid (when enabled)
    """
    # For MVP, API keys are not required
    # In production, uncomment this to enable authentication:
    #
    # if not x_api_key:
    #     raise HTTPException(
    #         status_code=status.HTTP_401_UNAUTHORIZED,
    #         detail="API key required"
    #     )
    #
    # # Validate API key against database
    # if not is_valid_api_key(x_api_key):
    #     raise HTTPException(
    #         status_code=status.HTTP_401_UNAUTHORIZED,
    #         detail="Invalid API key"
    #     )

    return x_api_key or "public"


def get_current_user():
    """
    Get current authenticated user.

    Placeholder for future authentication.
    """
    # For MVP, no authentication
    return {"user_id": "anonymous", "role": "public"}

from typing import Optional
from fastapi import Header
from src.config.settings import settings
from src.core.security import verify_api_key


async def require_api_key(
    x_api_key: Optional[str] = Header(None, alias=settings.api_key_header_name)
) -> bool:
    """Dependency that enforces API key authentication."""
    return verify_api_key(x_api_key)

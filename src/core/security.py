import hmac
from typing import Optional
from src.config.settings import settings
from src.core.exceptions import AuthenticationError


def verify_api_key(provided_key: Optional[str]) -> bool:
    """
    Verify the provided API key against configured secret using timing-safe comparison.
    """
    if not provided_key:
        raise AuthenticationError("API key header is missing.")

    # Use constant-time comparison to prevent timing attacks
    is_valid = hmac.compare_digest(
        provided_key.encode("utf-8"),
        settings.api_key_secret.encode("utf-8")
    )

    if not is_valid:
        raise AuthenticationError("Provided API key is invalid.")

    return True

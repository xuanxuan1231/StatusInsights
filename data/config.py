# env - config - hardcode

import os
from typing import Optional

from fastapi import HTTPException, Security, status
from fastapi.security import APIKeyHeader


def _env_bool(value: Optional[str]) -> bool:
    if value is None:
        return False
    return value.strip().lower() in {"1", "true", "yes", "y", "on"}


def _env_int(value: Optional[str], default: int) -> int:
    if value is None:
        return default
    try:
        return int(value)
    except ValueError:
        return default


MONGODB_ENABLED = _env_bool(os.getenv("MONGODB_ENABLED"))
MONGODB_URI = os.getenv("MONGODB_URI", "")
DEVICE_CACHE_TTL_SECONDS = _env_int(os.getenv("DEVICE_CACHE_TTL_SECONDS"), 5)
DEVICE_OFFLINE_THRESHOLD_SECONDS = _env_int(os.getenv("DEVICE_OFFLINE_THRESHOLD_SECONDS"), 20 * 60)

API_KEY_NAME = os.getenv("STATUSINSIGHTS_API_KEY_NAME", "X-API-Key")
API_KEY = os.getenv("STATUSINSIGHTS_API_KEY", "")

NAME = 'Wenxuan Shen'

_api_key_header = APIKeyHeader(name=API_KEY_NAME, auto_error=False)


def require_api_key(api_key: str = Security(_api_key_header)) -> str:
    if not API_KEY:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="API key not configured.",
        )
    if api_key != API_KEY:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key.",
        )
    return api_key

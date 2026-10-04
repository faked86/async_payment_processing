import secrets

from fastapi import Security, HTTPException, status
from fastapi.security import APIKeyHeader

from src.config.config import settings

api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


async def validate_api_key(api_key: str = Security(api_key_header)) -> str:
    if not api_key or not secrets.compare_digest(api_key, settings.api_key):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing API Key",
        )
    return api_key

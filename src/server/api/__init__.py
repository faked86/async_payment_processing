from fastapi import APIRouter, Depends

from src.server.api.deps import validate_api_key
from src.server.api.v1 import v1_router

api_router = APIRouter(prefix="/api", dependencies=[Depends(validate_api_key)])
api_router.include_router(v1_router)

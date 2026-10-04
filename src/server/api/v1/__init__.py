from fastapi import APIRouter

from src.server.api.v1.payments.views import payments_router

v1_router = APIRouter(prefix="/v1", tags=["v1"])
v1_router.include_router(payments_router)

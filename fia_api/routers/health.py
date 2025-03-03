from typing import Literal

from fastapi import APIRouter, HTTPException

from fia_api.core.repositories import test_connection

health_router = APIRouter()


@health_router.get("/healthz", tags=["health"])
async def get() -> Literal["ok"]:
    """Health Check endpoint."""
    return "ok"


@health_router.get("/ready", tags=["health"])
async def ready() -> Literal["ok"]:
    try:
        test_connection()
        return "ok"
    except Exception as e:
        raise HTTPException(status_code=503) from e

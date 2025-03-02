from typing import Literal

from fastapi import APIRouter, HTTPException

from fia_api.core.repositories import test_connection

k8s_router = APIRouter()


@k8s_router.get("/healthz", tags=["k8s"])
async def get() -> Literal["ok"]:
    """Health Check endpoint."""
    return "ok"


@k8s_router.get("/ready", tags=["k8s"])
async def ready() -> Literal["ok"]:
    try:
        test_connection()
        return "ok"
    except Exception as e:
        raise HTTPException(status_code=503) from e

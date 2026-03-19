import logging
from http import HTTPStatus
from typing import Annotated, Literal

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from fia_api.core.repositories import ensure_db_connection
from fia_api.core.session import get_db_session

health_router = APIRouter()
logger = logging.getLogger(__name__)


@health_router.get("/healthz", tags=["health"])
async def get() -> Literal["ok"]:
    """Health Check endpoint."""
    return "ok"


@health_router.get("/ready", tags=["health"])
async def ready(db: Annotated[Session, Depends(get_db_session)]) -> Literal["ok"]:
    try:
        ensure_db_connection(db)
        return "ok"
    except Exception as err:
        logger.exception("Database connection failed", exc_info=err)
        raise HTTPException(status_code=HTTPStatus.SERVICE_UNAVAILABLE) from err

# Live Data Script router
import os
from typing import Annotated, Literal

from fastapi import APIRouter, Depends
from fastapi.security import HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from fia_api.core.auth.tokens import JWTAPIBearer, get_user_from_token
from fia_api.core.cache import cache_get, cache_get_json, cache_set_json
from fia_api.core.exceptions import AuthError
from fia_api.core.request_models import LiveDataScriptUpdateRequest
from fia_api.core.services.instrument import (
    get_instruments_with_live_data_support,
    get_live_data_script_by_instrument_name,
    update_live_data_script_for_instrument,
)
from fia_api.core.session import get_db_session

LiveDataRouter = APIRouter(tags=["live-data"])
jwt_api_security = JWTAPIBearer()
LIVE_DATA_INSTRUMENTS_CACHE_TTL_SECONDS = int(os.environ.get("LIVE_DATA_INSTRUMENTS_CACHE_TTL_SECONDS", "120"))
LIVE_DATA_SCRIPT_CACHE_TTL_SECONDS = int(os.environ.get("LIVE_DATA_SCRIPT_CACHE_TTL_SECONDS", "60"))


@LiveDataRouter.get("/live-data/instruments")
async def get_live_data_instruments(session: Annotated[Session, Depends(get_db_session)]) -> list[str]:
    """
    Return a list of instrument names that support live data viewing.
    \f
    :param session: The current session of the request
    :return: List of instrument names with live data support enabled
    """
    cache_key = "fia_api:live_data:instruments"
    if LIVE_DATA_INSTRUMENTS_CACHE_TTL_SECONDS > 0:
        cached = cache_get_json(cache_key)
        if isinstance(cached, list):
            return cached

    instruments = get_instruments_with_live_data_support(session)

    if LIVE_DATA_INSTRUMENTS_CACHE_TTL_SECONDS > 0:
        cache_set_json(cache_key, instruments, LIVE_DATA_INSTRUMENTS_CACHE_TTL_SECONDS)

    return instruments


def _get_traceback_key(instrument: str) -> str:
    return f"live_data:{instrument.upper()}:traceback"


@LiveDataRouter.get("/live-data/{instrument}/traceback")
async def get_instrument_traceback(instrument: str) -> str | None:
    """
    Given an instrument string, return the live data traceback for that instrument if one exists
    \f
    :param instrument: The instrument string
    :return: The live data traceback or None
    """
    return cache_get(_get_traceback_key(instrument.lower()))


def _get_script_cache_key(instrument: str) -> str:
    return f"fia_api:live_data:script:{instrument.upper()}"


@LiveDataRouter.get("/live-data/{instrument}/script")
async def get_instrument_script(instrument: str, session: Annotated[Session, Depends(get_db_session)]) -> str | None:
    """
    Given an instrument string, return the live data script for that instrument
    \f
    :param instrument: The instrument string
    :param session: The current session of the request
    :return: The live data script or None
    """
    if LIVE_DATA_SCRIPT_CACHE_TTL_SECONDS > 0:
        cached = cache_get_json(_get_script_cache_key(instrument))
        if isinstance(cached, dict):
            return cached.get("script")

    script = get_live_data_script_by_instrument_name(instrument.upper(), session)

    if LIVE_DATA_SCRIPT_CACHE_TTL_SECONDS > 0:
        cache_set_json(_get_script_cache_key(instrument), {"script": script}, LIVE_DATA_SCRIPT_CACHE_TTL_SECONDS)

    return script


@LiveDataRouter.put("/live-data/{instrument}/script")
async def update_instrument_script(
    instrument: str,
    script_request: LiveDataScriptUpdateRequest,
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(jwt_api_security)],
    session: Annotated[Session, Depends(get_db_session)],
) -> Literal["ok"]:
    """
    Given an instrument string and a script request, update the live data script for that instrument
    \f
    :param instrument: The instrument string
    :param script_request: The json wrapped update request
    :param credentials: injected http authorization credentials
    :param session: The current session of the request
    :return:
    """
    user = get_user_from_token(credentials.credentials)
    if user.role != "staff":
        raise AuthError("Only Staff can update Live Data Scripts")

    update_live_data_script_for_instrument(instrument.upper(), script_request.value, session)
    # Clear traceback and script cache when script is updated
    cache_set_json(_get_traceback_key(instrument), None, 1)
    cache_set_json(_get_script_cache_key(instrument), None, 1)
    return "ok"

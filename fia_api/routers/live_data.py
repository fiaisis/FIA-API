# Live Data Script router
from typing import Annotated, Literal

from fastapi import APIRouter, Depends
from fastapi.security import HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from fia_api.core.auth.tokens import JWTAPIBearer, get_user_from_token
from fia_api.core.cache import cache_get_json, cache_set_json
from fia_api.core.exceptions import AuthError
from fia_api.core.request_models import LiveDataScriptUpdateRequest, LiveDataTracebackUpdateRequest
from fia_api.core.services.instrument import (
    get_instruments_with_live_data_support,
    get_live_data_script_by_instrument_name,
    update_live_data_script_for_instrument,
)
from fia_api.core.session import get_db_session

LiveDataRouter = APIRouter(tags=["live-data"])
jwt_api_security = JWTAPIBearer()


@LiveDataRouter.get("/live-data/instruments")
async def get_live_data_instruments(session: Annotated[Session, Depends(get_db_session)]) -> list[str]:
    """
    Return a list of instrument names that support live data viewing.
    \f
    :param session: The current session of the request
    :return: List of instrument names with live data support enabled
    """
    return get_instruments_with_live_data_support(session)


def _get_traceback_key(instrument: str) -> str:
    return f"fia_api:live_data:traceback:{instrument.upper()}"


@LiveDataRouter.get("/live-data/{instrument}/traceback")
async def get_instrument_traceback(instrument: str) -> str | None:
    """
    Given an instrument string, return the live data traceback for that instrument if one exists
    \f
    :param instrument: The instrument string
    :return: The live data traceback or None
    """
    return cache_get_json(_get_traceback_key(instrument))


@LiveDataRouter.post("/live-data/{instrument}/traceback")
async def update_instrument_traceback(
    instrument: str,
    traceback_request: LiveDataTracebackUpdateRequest,
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(jwt_api_security)],
) -> Literal["ok"]:
    """
    Given an instrument string and a traceback request, update the live data traceback for that instrument
    \f
    :param instrument: The instrument string
    :param traceback_request: The json wrapped update request
    :param credentials: injected http authorization credentials
    :return:
    """
    # Only allow reporting if authenticated (either by user or API key)
    # The processor uses FIA_API_API_KEY which gives it staff role
    user = get_user_from_token(credentials.credentials)
    if user.role != "staff":
        raise AuthError("Only Staff can update Live Data Tracebacks")

    # Store in Valkey with 24 hour TTL
    cache_set_json(_get_traceback_key(instrument), traceback_request.value, 60 * 60 * 24)
    return "ok"


@LiveDataRouter.get("/live-data/{instrument}/script")
async def get_instrument_script(instrument: str, session: Annotated[Session, Depends(get_db_session)]) -> str | None:
    """
    Given an instrument string, return the live data script for that instrument
    \f
    :param instrument: The instrument string
    :param session: The current session of the request
    :return: The live data script or None
    """
    return get_live_data_script_by_instrument_name(instrument.upper(), session)


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
    # Clear traceback when script is updated
    cache_set_json(_get_traceback_key(instrument), None, 1)
    return "ok"

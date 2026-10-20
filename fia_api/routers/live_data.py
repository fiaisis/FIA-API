# Live Data Script router
from typing import Annotated, Literal

from fastapi import APIRouter, Depends
from fastapi.security import HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from starlette.responses import StreamingResponse

from fia_api.core.auth.tokens import JWTAPIBearer, get_user_from_token
from fia_api.core.cache import log_stream_generator
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


@LiveDataRouter.get("/live-data/instruments")
async def get_live_data_instruments(session: Annotated[Session, Depends(get_db_session)]) -> list[str]:
    """
    Return a list of instrument names that support live data viewing.
    \f
    :param session: The current session of the request
    :return: List of instrument names with live data support enabled
    """
    return get_instruments_with_live_data_support(session)


@LiveDataRouter.get("/live-data/{instrument_name}/logs")
async def stream_logs(
    _: Annotated[HTTPAuthorizationCredentials, Depends(jwt_api_security)],
    instrument_name: str,
    since: str = "0",
) -> StreamingResponse:
    """
    Server-Sent Events (SSE) endpoint to stream live logs from Valkey.
    """
    return StreamingResponse(
        log_stream_generator(instrument_name, since),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


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

    return "ok"

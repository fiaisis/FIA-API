# Live Data Script router
from typing import Annotated, Literal

from fastapi import APIRouter, Depends
from fastapi.security import HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from fia_api.core.auth.tokens import JWTAPIBearer, get_user_from_token
from fia_api.core.exceptions import AuthError
from fia_api.core.request_models import LiveDataScriptUpdateRequest
from fia_api.core.services.instrument import (
    get_live_data_script_by_instrument_name,
    update_live_data_script_for_instrument,
)
from fia_api.core.session import get_db_session

LiveDataRouter = APIRouter(tags=["live-data"])
jwt_api_security = JWTAPIBearer()


@LiveDataRouter.get("/live-data/{instrument}/script")
async def get_instrument_script(instrument: str, db: Annotated[Session, Depends(get_db_session)]) -> str | None:
    """
    Given an instrument string, return the live data script for that instrument
    \f
    :param instrument: The instrument string
    :param db: The current session of the request
    :return: The live data script or None
    """
    return get_live_data_script_by_instrument_name(instrument.upper(), db)


@LiveDataRouter.put("/live-data/{instrument}/script")
async def update_instrument_script(
    instrument: str,
    script_request: LiveDataScriptUpdateRequest,
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(jwt_api_security)],
    db: Annotated[Session, Depends(get_db_session)],
) -> Literal["ok"]:
    """
    Given an instrument string and a script request, update the live data script for that instrument
    \f
    :param instrument: The instrument string
    :param script_request: The json wrapped update request
    :param credentials: injected http authorization credentials
    :param db: The current session of the request
    :return:
    """
    user = get_user_from_token(credentials.credentials)
    if user.role != "staff":
        raise AuthError("Only Staff can update Live Data Scripts")

    update_live_data_script_for_instrument(instrument.upper(), script_request.value, db)
    return "ok"

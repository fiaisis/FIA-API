# Live Data Script router
from typing import Annotated, Literal

from fastapi import APIRouter, Depends
from fastapi.security import HTTPAuthorizationCredentials

from fia_api.core.auth.tokens import JWTAPIBearer, get_user_from_token
from fia_api.core.exceptions import AuthError
from fia_api.core.models import InstrumentString
from fia_api.core.request_models import LiveDataScriptUpdateRequest
from fia_api.scripts.live_data import LiveDataScript

LiveDataRouter = APIRouter(tags=["live-data"])
jwt_api_security = JWTAPIBearer()


@LiveDataRouter.get("/live-data/{instrument}/script")
async def get_instrument_script(instrument: InstrumentString) -> str:
    """
    Given an instrument string, return the live data script for that instrument
    \f
    :param instrument: The instrument string
    :return: The live data script
    """
    return LiveDataScript(instrument).value


@LiveDataRouter.put("/live-data/{instrument}/script")
async def update_instrument_script(
    instrument: InstrumentString,
    script_request: LiveDataScriptUpdateRequest,
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(jwt_api_security)],
) -> Literal["ok"]:
    """
    Given an instrument string and a script request, update the live data script for that instrument
    \f
    :param instrument: The instrument string
    :param script_request: The json wrapped update request
    :param credentials: injected http authorization credentials
    :return:
    """
    user = get_user_from_token(credentials.credentials)
    if user.role != "staff":
        raise AuthError("Only Staff can update Live Data Scripts")

    LiveDataScript(instrument).update(script_request.value)
    return "ok"

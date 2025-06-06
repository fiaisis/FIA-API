from http import HTTPStatus
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials

from fia_api.core.auth.tokens import JWTAPIBearer, get_user_from_token
from fia_api.core.services.instrument import get_latest_run_by_instrument_name, update_latest_run_for_instrument

InstrumentRouter = APIRouter(prefix="/instrument")
jwt_api_security = JWTAPIBearer()


@InstrumentRouter.get("/{instrument}/latest-run", tags=["instrument"])
async def get_instrument_latest_run(
    instrument: str, credentials: Annotated[HTTPAuthorizationCredentials, Depends(jwt_api_security)]
) -> dict[str, str | None]:
    """
    Return the latest run for the given instrument
    \f
    :param instrument: The instrument name
    :return: The latest run
    """
    user = get_user_from_token(credentials.credentials)
    if user.role != "staff":
        # If not staff this is not allowed
        raise HTTPException(status_code=HTTPStatus.FORBIDDEN)
    latest_run = get_latest_run_by_instrument_name(instrument.upper())
    return {"latest_run": latest_run}


@InstrumentRouter.put("/{instrument}/latest-run", tags=["instrument"])
async def update_instrument_latest_run(
    instrument: str,
    latest_run: dict[str, str],
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(jwt_api_security)],
) -> dict[str, str]:
    """
    Update the latest run for the given instrument
    \f
    :param instrument: The instrument name
    :param latest_run: The latest run as a JSON object with a 'latest_run' field
    :return: The updated latest run
    """
    user = get_user_from_token(credentials.credentials)
    if user.role != "staff":
        # If not staff this is not allowed
        raise HTTPException(status_code=HTTPStatus.FORBIDDEN)
    update_latest_run_for_instrument(instrument.upper(), latest_run["latest_run"])
    return {"latest_run": latest_run["latest_run"]}

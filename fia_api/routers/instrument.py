import os
from typing import Annotated

from fastapi import APIRouter, Depends
from fastapi.security import HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from fia_api.core.auth.tokens import JWTAPIBearer, get_user_from_token
from fia_api.core.cache import cache_get_json, cache_set_json
from fia_api.core.exceptions import AuthError
from fia_api.core.services.instrument import get_latest_run_by_instrument_name, update_latest_run_for_instrument
from fia_api.core.session import get_db_session

InstrumentRouter = APIRouter(prefix="/instrument")
jwt_api_security = JWTAPIBearer()
INSTRUMENT_LATEST_RUN_CACHE_TTL_SECONDS = int(os.environ.get("INSTRUMENT_LATEST_RUN_CACHE_TTL_SECONDS", "15"))


def _latest_run_cache_key(instrument: str) -> str:
    return f"fia_api:instrument:latest_run:{instrument.upper()}"


@InstrumentRouter.get("/{instrument}/latest-run", tags=["instrument"])
async def get_instrument_latest_run(
    instrument: str,
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(jwt_api_security)],
    session: Annotated[Session, Depends(get_db_session)],
) -> dict[str, str | None]:
    """
    Return the latest run for the given instrument
    \f
    :param instrument: The instrument name
    :param session: The current session of the request
    :return: The latest run
    """
    user = get_user_from_token(credentials.credentials)
    if user.role != "staff":
        # If not staff this is not allowed
        raise AuthError("User not authorised for this action")

    if INSTRUMENT_LATEST_RUN_CACHE_TTL_SECONDS > 0:
        cached = cache_get_json(_latest_run_cache_key(instrument))
        if isinstance(cached, dict):
            return cached

    latest_run = get_latest_run_by_instrument_name(instrument.upper(), session)
    payload = {"latest_run": latest_run}

    if INSTRUMENT_LATEST_RUN_CACHE_TTL_SECONDS > 0:
        cache_set_json(_latest_run_cache_key(instrument), payload, INSTRUMENT_LATEST_RUN_CACHE_TTL_SECONDS)

    return payload


@InstrumentRouter.put("/{instrument}/latest-run", tags=["instrument"])
async def update_instrument_latest_run(
    instrument: str,
    latest_run: dict[str, str],
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(jwt_api_security)],
    session: Annotated[Session, Depends(get_db_session)],
) -> dict[str, str]:
    """
    Update the latest run for the given instrument
    \f
    :param instrument: The instrument name
    :param latest_run: The latest run as a JSON object with a 'latest_run' field
    :param credentials: Dependency Injected credentials
    :param session: The current session of the request
    :return: The updated latest run
    """
    user = get_user_from_token(credentials.credentials)
    if user.role != "staff":
        # If not staff this is not allowed
        raise AuthError("User not authorised for this action")
    update_latest_run_for_instrument(instrument.upper(), latest_run["latest_run"], session)
    cache_set_json(_latest_run_cache_key(instrument), None, 1)
    return {"latest_run": latest_run["latest_run"]}

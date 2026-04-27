import os
from typing import Annotated, Any

from fastapi import APIRouter, Depends
from fastapi.security import HTTPAuthorizationCredentials
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Session

from fia_api.core.auth.tokens import JWTAPIBearer, get_user_from_token
from fia_api.core.cache import cache_get_json, cache_set_json
from fia_api.core.exceptions import AuthError
from fia_api.core.services.instrument import get_specification_by_instrument_name, update_specification_for_instrument
from fia_api.core.session import get_db_session

InstrumentSpecRouter = APIRouter()
jwt_api_security = JWTAPIBearer()
INSTRUMENT_SPEC_CACHE_TTL_SECONDS = int(os.environ.get("INSTRUMENT_SPEC_CACHE_TTL_SECONDS", "120"))


def _spec_cache_key(instrument_name: str) -> str:
    return f"fia_api:instrument:spec:{instrument_name.upper()}"


@InstrumentSpecRouter.get(
    "/instrument/{instrument_name}/specification", tags=["instrument specifications"], response_model=None
)
async def get_instrument_specification(
    instrument_name: str,
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(jwt_api_security)],
    session: Annotated[Session, Depends(get_db_session)],
) -> JSONB | None:
    """
    Return the specification for the given instrument
    \f
    :param instrument_name: The instrument
    :return: The specification
    """
    user = get_user_from_token(credentials.credentials)
    if user.role != "staff":
        # If not staff this is not allowed
        raise AuthError("User not authorised for this action")

    if INSTRUMENT_SPEC_CACHE_TTL_SECONDS > 0:
        cached = cache_get_json(_spec_cache_key(instrument_name))
        if isinstance(cached, dict):
            return cached.get("specification")

    specification = get_specification_by_instrument_name(instrument_name.upper(), session)

    if INSTRUMENT_SPEC_CACHE_TTL_SECONDS > 0:
        cache_set_json(
            _spec_cache_key(instrument_name), {"specification": specification}, INSTRUMENT_SPEC_CACHE_TTL_SECONDS
        )

    return specification


@InstrumentSpecRouter.put("/instrument/{instrument_name}/specification", tags=["instrument specifications"])
async def update_instrument_specification(
    instrument_name: str,
    specification: dict[str, Any],
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(jwt_api_security)],
    session: Annotated[Session, Depends(get_db_session)],
) -> dict[str, Any]:
    """
    Replace the current specification with the given specification for the given instrument
    \f
    :param instrument_name: The instrument name
    :param specification: The new specification
    :return: The new specification
    """
    user = get_user_from_token(credentials.credentials)
    if user.role != "staff":
        # If not staff this is not allowed
        raise AuthError("User not authorised for this action")
    update_specification_for_instrument(instrument_name.upper(), specification, session)
    cache_set_json(_spec_cache_key(instrument_name), None, 1)
    return specification

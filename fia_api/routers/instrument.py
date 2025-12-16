from typing import Annotated

from fastapi import APIRouter, Depends
from fastapi.security import HTTPAuthorizationCredentials

from fia_api.core.auth.tokens import JWTAPIBearer, get_user_from_token
from fia_api.core.exceptions import AuthError
from fia_api.core.services.instrument import get_latest_run_by_instrument_name, update_latest_run_for_instrument
from fia_api.core.session import get_db_session
from sqlalchemy.orm import Session

InstrumentRouter = APIRouter(prefix="/instrument")
jwt_api_security = JWTAPIBearer()


@InstrumentRouter.get("/{instrument}/latest-run", tags=["instrument"])
async def get_instrument_latest_run(
    instrument: str, credentials: Annotated[HTTPAuthorizationCredentials, Depends(jwt_api_security)], db: Session = Depends(get_db_session)
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
        raise AuthError("User not authorised for this action")
    latest_run = get_latest_run_by_instrument_name(instrument.upper(), db)
    return {"latest_run": latest_run}


@InstrumentRouter.put("/{instrument}/latest-run", tags=["instrument"])
async def update_instrument_latest_run(
    instrument: str,
    latest_run: dict[str, str],
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(jwt_api_security)],
    db: Session = Depends(get_db_session)
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
        raise AuthError("User not authorised for this action")
    update_latest_run_for_instrument(instrument.upper(), latest_run["latest_run"], db)
    return {"latest_run": latest_run["latest_run"]}

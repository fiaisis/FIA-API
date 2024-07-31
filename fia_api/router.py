"""
Module containing the REST endpoints
"""

from __future__ import annotations

from typing import Annotated, Any, Literal

from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials
from sqlalchemy.dialects.postgresql import JSONB
from starlette.background import BackgroundTasks

from fia_api.core.auth.api_keys import APIKeyBearer
from fia_api.core.auth.tokens import JWTBearer, get_user_from_token
from fia_api.core.repositories import test_connection
from fia_api.core.responses import (
    CountResponse,
    PreScriptResponse,
    ReductionResponse,
    ReductionWithRunsResponse,
)
from fia_api.core.services.instrument import get_specification_by_instrument_name, update_specification_for_instrument
from fia_api.core.services.reduction import (
    count_reductions,
    count_reductions_by_instrument,
    get_all_reductions,
    get_reduction_by_id,
    get_reductions_by_instrument,
)
from fia_api.scripts.acquisition import (
    get_script_by_sha,
    get_script_for_reduction,
    write_script_locally,
)
from fia_api.scripts.pre_script import PreScript

ROUTER = APIRouter()
jwt_security = JWTBearer()
api_key_security = APIKeyBearer()


@ROUTER.get("/healthz", tags=["k8s"])
async def get() -> Literal["ok"]:
    """Health Check endpoint."""
    return "ok"

@ROUTER.get("/ready", tags=["k8s"])
async def ready() -> Literal["ok"]:
    try:
        test_connection()
        return "ok"
    except Exception as e:
        raise HTTPException(status_code=503) from e

@ROUTER.get("/instrument/{instrument}/script", tags=["scripts"])
async def get_pre_script(
    instrument: str,
    background_tasks: BackgroundTasks,
    reduction_id: int | None = None,
) -> PreScriptResponse:
    """
    Script URI - Not intended for calling
    \f
    :param instrument: the instrument
    :param background_tasks: handled by fastapi
    :param reduction_id: optional query parameter of runfile, used to apply transform
    :return: ScriptResponse
    """
    script = PreScript(value="")
    # This will never be returned from the api, but is necessary for the background task to run
    try:
        script = get_script_for_reduction(instrument, reduction_id)
        return script.to_response()
    finally:
        background_tasks.add_task(write_script_locally, script, instrument)
        # write the script after to not slow down request


@ROUTER.get("/instrument/{instrument}/script/sha/{sha}", tags=["scripts"])
async def get_pre_script_by_sha(instrument: str, sha: str, reduction_id: int | None = None) -> PreScriptResponse:
    """
    Given an instrument and the commit sha of a script, obtain the pre script. Optionally providing a reduction id to
    transform the script
    \f
    :param instrument: The instrument
    :param sha: The commit sha of the script
    :param reduction_id: The reduction id to apply transforms
    :return:
    """
    return get_script_by_sha(instrument, sha, reduction_id).to_response()


OrderField = Literal[
    "reduction_start",
    "reduction_end",
    "reduction_state",
    "id",
    "run_start",
    "run_end",
    "reduction_outputs",
    "experiment_number",
    "experiment_title",
    "filename",
]


@ROUTER.get("/reductions", tags=["reductions"])
async def get_reductions(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(jwt_security)],
    limit: int = 0,
    offset: int = 0,
    order_by: OrderField = "reduction_start",
    order_direction: Literal["asc", "desc"] = "desc",
    include_runs: bool = False,
) -> list[ReductionResponse] | list[ReductionWithRunsResponse]:
    """
    Retrieve all reductions.
    \f
    :param credentials: Dependency injected HTTPAuthorizationCredentials
    :param limit: optional limit for the number of reductions returned (default is 0, which can be interpreted as
    no limit)
    :param offset: optional offset for the list of reductions (default is 0)
    :param order_by: Literal["reduction_start", "reduction_end", "reduction_state", "id"]
    :param order_direction: Literal["asc", "desc"]
    :param include_runs: bool
    :return: List of ReductionResponse objects
    """
    user = get_user_from_token(credentials.credentials)
    user_number = None if user.role == "staff" else user.user_number
    reductions = get_all_reductions(
        limit=limit, offset=offset, order_by=order_by, order_direction=order_direction, user_number=user_number
    )

    if include_runs:
        return [ReductionWithRunsResponse.from_reduction(r) for r in reductions]
    return [ReductionResponse.from_reduction(r) for r in reductions]


@ROUTER.get("/instrument/{instrument}/reductions", tags=["reductions"])
async def get_reductions_for_instrument(
    instrument: str,
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(jwt_security)],
    limit: int = 0,
    offset: int = 0,
    order_by: OrderField = "reduction_start",
    order_direction: Literal["asc", "desc"] = "desc",
    include_runs: bool = False,
) -> list[ReductionResponse] | list[ReductionWithRunsResponse]:
    """
    Retrieve a list of reductions for a given instrument.
    \f
    :param credentials: Dependency injected HTTPAuthorizationCredentials
    :param instrument: the name of the instrument
    :param limit: optional limit for the number of reductions returned (default is 0, which can be interpreted as
    no limit)
    :param offset: optional offset for the list of reductions (default is 0)
    :param order_by: Literal["reduction_start", "reduction_end", "reduction_state", "id"]
    :param order_direction: Literal["asc", "desc"]
    :param include_runs: bool
    :return: List of ReductionResponse objects
    """
    user = get_user_from_token(credentials.credentials)
    instrument = instrument.upper()
    user_number = None if user.role == "staff" else user.user_number
    reductions = get_reductions_by_instrument(
        instrument,
        limit=limit,
        offset=offset,
        order_by=order_by,
        order_direction=order_direction,
        user_number=user_number,
    )

    if include_runs:
        return [ReductionWithRunsResponse.from_reduction(r) for r in reductions]
    return [ReductionResponse.from_reduction(r) for r in reductions]


@ROUTER.get("/instrument/{instrument}/reductions/count", tags=["reductions"])
async def count_reductions_for_instrument(
    instrument: str,
) -> CountResponse:
    """
    Count reductions for a given instrument.
    \f
    :param instrument: the name of the instrument
    :return: List of ReductionResponse objects
    """
    instrument = instrument.upper()
    return CountResponse(count=count_reductions_by_instrument(instrument))


@ROUTER.get("/reduction/{reduction_id}", tags=["reductions"])
async def get_reduction(
    reduction_id: int, credentials: Annotated[HTTPAuthorizationCredentials, Depends(jwt_security)]
) -> ReductionWithRunsResponse:
    """
    Retrieve a reduction with nested run data, by iD.
    \f
    :param reduction_id: the unique identifier of the reduction
    :return: ReductionWithRunsResponse object
    """
    user = get_user_from_token(credentials.credentials)
    if user.role == "staff":
        reduction = get_reduction_by_id(reduction_id)
    else:
        reduction = get_reduction_by_id(reduction_id, user_number=user.user_number)
    return ReductionWithRunsResponse.from_reduction(reduction)


@ROUTER.get("/reductions/count", tags=["reductions"])
async def count_all_reductions() -> CountResponse:
    """
    Count all reductions
    \f
    :return: CountResponse containing the count
    """
    return CountResponse(count=count_reductions())


@ROUTER.get("/instrument/{instrument_name}/specification", tags=["instrument"], response_model=None)
async def get_instrument_specification(
    instrument_name: str, _: Annotated[HTTPAuthorizationCredentials, Depends(api_key_security)]
) -> JSONB:
    """
    Return the specification for the given instrument
    \f
    :param instrument_name: The instrument
    :return: The specificaiton
    """
    return get_specification_by_instrument_name(instrument_name.upper())


@ROUTER.put("/instrument/{instrument_name}/specification", tags=["instrument"])
async def update_instrument_specification(
    instrument_name: str,
    specification: dict[str, Any],
    _: Annotated[HTTPAuthorizationCredentials, Depends(api_key_security)],
) -> dict[str, Any]:
    """
    Replace the current specification with the given specification for the given instrument
    \f
    :param instrument_name: The instrument name
    :param specification: The new specification
    :return: The new specification
    """
    update_specification_for_instrument(instrument_name.upper(), specification)
    return specification

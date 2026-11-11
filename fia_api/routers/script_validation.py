"""Script validation router forwarding editor diagnostics requests to mantid-python-script-lsp."""

from __future__ import annotations

import asyncio
from typing import Annotated

from fastapi import APIRouter, Depends
from fastapi.security import HTTPAuthorizationCredentials
from starlette.responses import JSONResponse

from fia_api.core.auth.tokens import JWTAPIBearer, get_user_from_token
from fia_api.core.request_models import AnalyseRequest
from fia_api.core.services.script_validation import analyse_script_for_user

ScriptValidationRouter = APIRouter(prefix="/script", tags=["script"])
jwt_api_security = JWTAPIBearer()


@ScriptValidationRouter.post("/analyse")
async def analyse_script(
    request: AnalyseRequest,
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(jwt_api_security)],
) -> JSONResponse:
    """
    Validate a Python reduction or live-data script without executing it.

    Available to any authenticated user. Forwards the response status and body from
    `mantid-python-script-lsp` unchanged so the frontend can distinguish `200`, `422`, `429`, and `503`.
    """
    user = get_user_from_token(credentials.credentials)
    result = await asyncio.to_thread(analyse_script_for_user, request, user.user_number)
    headers = {} if result.retry_after_seconds is None else {"Retry-After": str(result.retry_after_seconds)}
    return JSONResponse(status_code=result.status_code, content=result.body, headers=headers)

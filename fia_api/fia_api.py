"""Main module contains the uvicorn entrypoint"""

import logging
import os
import sys

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.middleware.cors import CORSMiddleware

from fia_api.core.exceptions import (
    AuthError,
    JobRequestError,
    MissingRecordError,
    MissingScriptError,
    NoFilesAddedError,
    UnsafePathError,
)
from fia_api.exception_handlers import (
    authentication_error_handler,
    bad_job_request_handler,
    missing_record_handler,
    missing_script_handler,
    unsafe_path_handler,
    validation_exception_handler,
)
from fia_api.routers.extras import ExtrasRouter
from fia_api.routers.find_file import FindFileRouter
from fia_api.routers.health import health_router
from fia_api.routers.instrument import InstrumentRouter
from fia_api.routers.instrument_specs import InstrumentSpecRouter
from fia_api.routers.job_creation import JobCreationRouter
from fia_api.routers.jobs import JobsRouter
from fia_api.routers.live_data import LiveDataRouter


class EndpointFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        return record.getMessage().find("/healthz") == -1 and record.getMessage().find("/ready") == -1

async def no_files_added_handler(_: Request, exc: NoFilesAddedError):
    return JSONResponse(
        status_code=404,
        content={
            "detail": "None of the requested files could be found.",
            "missing_files_count": len(exc.missing_files),
            "missing_files": exc.missing_files,
        },
        headers={
            "x-missing-files-count": str(len(exc.missing_files)),
            "x-missing-files": ";".join(exc.missing_files),
        },
    )



stdout_handler = logging.StreamHandler(stream=sys.stdout)
logging.basicConfig(
    handlers=[stdout_handler],
    format="[%(asctime)s]-%(name)s-%(levelname)s: %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)
logging.getLogger("uvicorn.access").addFilter(EndpointFilter())

DEV_MODE = bool(os.environ.get("DEV_MODE", False))  # noqa: PLW1508

app = FastAPI(title="FIA API", root_path="/" if DEV_MODE else "/api")

# This must be updated before exposing outside the vpn
ALLOWED_ORIGINS = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(ExtrasRouter)
app.include_router(InstrumentRouter)
app.include_router(InstrumentSpecRouter)
app.include_router(JobCreationRouter)
app.include_router(JobsRouter)
app.include_router(health_router)
app.include_router(FindFileRouter)
app.include_router(LiveDataRouter)

app.add_exception_handler(MissingRecordError, missing_record_handler)
app.add_exception_handler(MissingScriptError, missing_script_handler)
app.add_exception_handler(UnsafePathError, unsafe_path_handler)
app.add_exception_handler(AuthError, authentication_error_handler)
app.add_exception_handler(JobRequestError, bad_job_request_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(NoFilesAddedError, no_files_added_handler)

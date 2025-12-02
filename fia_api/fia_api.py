"""Main module contains the uvicorn entrypoint"""

import logging
import os
import sys

from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from starlette.middleware.cors import CORSMiddleware

from fia_api.core.exceptions import (
    AuthError,
    BadRequestError,
    DataIntegrityError,
    GithubAPIRequestError,
    JobOwnerError,
    JobRequestError,
    MissingRecordError,
    MissingScriptError,
    NoFilesAddedError,
    ReadDirError,
    UnsafePathError,
    UploadFileError,
)
from fia_api.exception_handlers import (
    authentication_error_handler,
    bad_job_request_handler,
    bad_request_handler,
    data_integrity_handler,
    github_api_request_handler,
    job_owner_err_handler,
    missing_record_handler,
    missing_script_handler,
    no_files_added_handler,
    read_dir_err_handler,
    unsafe_path_handler,
    upload_file_err_handler,
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

DEV_MODE = bool(os.environ.get("DEV_MODE", False))  # noqa: PLW1508


class EndpointFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        return record.getMessage().find("/healthz") == -1 and record.getMessage().find("/ready") == -1


stdout_handler = logging.StreamHandler(stream=sys.stdout)
logging.basicConfig(
    handlers=[stdout_handler],
    format="[%(asctime)s]-%(name)s-%(levelname)s: %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)
logging.getLogger("uvicorn.access").addFilter(EndpointFilter())

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
app.add_exception_handler(ReadDirError, read_dir_err_handler)
app.add_exception_handler(UploadFileError, upload_file_err_handler)
app.add_exception_handler(GithubAPIRequestError, github_api_request_handler)
app.add_exception_handler(BadRequestError, bad_request_handler)
app.add_exception_handler(DataIntegrityError, data_integrity_handler)
app.add_exception_handler(JobOwnerError, job_owner_err_handler)

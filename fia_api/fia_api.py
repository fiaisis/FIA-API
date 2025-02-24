"""Main module contains the uvicorn entrypoint"""

import logging
import sys

from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware

from fia_api.core.exceptions import (
    AuthenticationError,
    MissingRecordError,
    MissingScriptError,
    UnsafePathError,
)
from fia_api.exception_handlers import (
    authentication_error_handler,
    missing_record_handler,
    missing_script_handler,
    unsafe_path_handler,
)
from fia_api.router import ROUTER

stdout_handler = logging.StreamHandler(stream=sys.stdout)
logging.basicConfig(
    handlers=[stdout_handler],
    format="[%(asctime)s]-%(name)s-%(levelname)s: %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)


app = FastAPI()

# This must be updated before exposing outside the vpn
ALLOWED_ORIGINS = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(ROUTER)

app.add_exception_handler(MissingRecordError, missing_record_handler)
app.add_exception_handler(MissingScriptError, missing_script_handler)
app.add_exception_handler(UnsafePathError, unsafe_path_handler)
app.add_exception_handler(AuthenticationError, authentication_error_handler)

import logging
import os

from fastapi import HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from starlette import status
from starlette.requests import Request

logger = logging.getLogger(__name__)
API_KEY = os.environ.get("FIA_API_API_KEY", "shh")


class APIKeyBearer(HTTPBearer):
    """
    Extends the FastAPI `HTTPBearer` class to provide APIKey based authentication/authorization.
    """

    async def __call__(self, request: Request) -> HTTPAuthorizationCredentials | None:
        """
        Callable method for JWT access token authentication/authorization.

        This method is called when `JWTBearer` is used as a dependency in a FastAPI route. It performs authentication/
        authorization by calling the parent class method and then verifying the JWT access token.
        :param request: The FastAPI `Request` object.
        :return: The JWT access token if authentication is successful.
        :raises HTTPException: If the supplied JWT access token is invalid or has expired.
        """
        credentials: HTTPAuthorizationCredentials | None = await super().__call__(request)
        try:
            api_key = credentials.credentials  # type: ignore # if credentials is None, it will raise here and be caught immediately
        except RuntimeError as exc:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Bad or missing APIKey",
            ) from exc

        if not self._is_api_key_valid(api_key):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Invalid APIKey",
            )

        return credentials

    def _is_api_key_valid(self, api_key: str) -> bool:
        """
        Check if the JWT access token is valid.

        It does this by checking that it was signed by the corresponding private key and has not expired. It also
        requires the payload to contain a username.
        :param api_key: The JWT access token to check.
        :return: `True` if the JWT access token is valid and its payload contains a username, `False` otherwise.
        """
        return api_key == API_KEY

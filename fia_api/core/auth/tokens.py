import logging
import os
from dataclasses import dataclass
from http import HTTPStatus
from typing import Literal

import jwt
import requests
from fastapi import Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from fia_api.core.auth import AUTH_URL
from fia_api.core.exceptions import AuthError

logger = logging.getLogger(__name__)

DEV_MODE = bool(os.environ.get("DEV_MODE", False))  # noqa: PLW1508


@dataclass
class User:
    user_number: int
    role: Literal["staff", "user"]


def get_user_from_token(token: str) -> User:
    if DEV_MODE:
        return User(user_number=123, role="staff")
    api_key = os.environ["FIA_API_API_KEY"]
    if token == api_key:
        return User(user_number=-1, role="staff")
    try:
        payload = jwt.decode(
            token, options={"verify_signature": False}
        )  # We don't verify here as it is verified by the auth api previously when the token is obtained via the
        # JWTAPIBearer class below
        return User(user_number=payload.get("usernumber"), role=payload.get("role"))
    except RuntimeError as exc:
        raise AuthError("Problem unpacking jwt token") from exc


class JWTAPIBearer(HTTPBearer):
    """Extends the FastAPI `HTTPBearer` class to provide JSON Web Token (JWT) based authentication/authorization."""

    async def __call__(self, request: Request) -> HTTPAuthorizationCredentials | None:
        """
        Callable method for JWT access token authentication/authorization.

        This method is called when `JWTAPIBearer` is used as a dependency in a FastAPI route. It performs
        authentication/authorization by calling the parent class method and then verifying the JWT access
        token also checks if the value received as a valid API Key.
        :param request: The FastAPI `Request` object.
        :return: The JWT access token if authentication is successful.
        :raises AuthError: If the supplied JWT access token or the API key is invalid or has expired.
        """
        if DEV_MODE:
            return HTTPAuthorizationCredentials(scheme="Bearer", credentials="foo")
        credentials: HTTPAuthorizationCredentials | None = await super().__call__(request)
        try:
            token = credentials.credentials  # type: ignore # if credentials is None, it will raise here and be caught immediately
        except RuntimeError as exc:
            raise AuthError("Invalid token or expired token") from exc

        if self._is_api_key_valid(token) or self._is_jwt_access_token_valid(token):
            return credentials

        raise AuthError("Invalid token, expired token or invalid API key")

    @staticmethod
    def _is_jwt_access_token_valid(access_token: str) -> bool:
        """
        Check if the JWT access token is valid.

        It does this by checking that it was signed by the corresponding private key and has not expired. It also
        requires the payload to contain a username.
        :param access_token: The JWT access token to check.
        :return: `True` if the JWT access token is valid and its payload contains a username, `False` otherwise.
        """
        logger.info("Checking if JWT access token is valid")
        try:
            response = requests.post(f"{AUTH_URL}/api/jwt/checkToken", json={"token": access_token}, timeout=30)
            if response.status_code == HTTPStatus.OK:
                logger.info("JWT was valid")
                return True
            return False
        except RuntimeError:
            logger.exception("Error decoding JWT access token")
            return False

    @staticmethod
    def _is_api_key_valid(api_key: str) -> bool:
        """
        Check if the API key is valid.

        It does this by checking that it was signed by the corresponding private key and has not expired.
        :param api_key: The API key to check.
        :return: `True` if the API key is valid, `False` otherwise.
        """
        env_api_key = os.environ["FIA_API_API_KEY"]
        return api_key == env_api_key

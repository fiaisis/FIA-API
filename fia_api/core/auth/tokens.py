import logging
from dataclasses import dataclass
from http import HTTPStatus
from typing import Literal

import jwt
import requests
from fastapi import HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from fia_api.core.auth import AUTH_URL
from fia_api.core.exceptions import AuthenticationError

logger = logging.getLogger(__name__)


@dataclass
class User:
    user_number: int
    role: Literal["staff", "user"]


def get_user_from_token(token: str) -> User:
    try:
        payload = jwt.decode(token, options={"verify_signature": False})
        return User(user_number=payload.get("usernumber"), role=payload.get("role"))
    except RuntimeError as exc:
        raise AuthenticationError("Problem unpacking jwt token") from exc


class JWTBearer(HTTPBearer):
    """
    Extends the FastAPI `HTTPBearer` class to provide JSON Web Token (JWT) based authentication/authorization.
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
            token = credentials.credentials  # type: ignore # if credentials is None, it will raise here and be caught immediately
        except RuntimeError as exc:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid token or expired token") from exc

        if not self._is_jwt_access_token_valid(token):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid token or expired token")

        return credentials

    def _is_jwt_access_token_valid(self, access_token: str) -> bool:
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
        except RuntimeError:  # pylint: disable=broad-exception-caught)
            logger.exception("Error decoding JWT access token")
            return False

from http import HTTPStatus
from typing import Any, Optional, Union, cast

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.http_validation_error import HTTPValidationError
from ...types import UNSET, Response


def _get_kwargs(
    experiment_number: int,
    *,
    filename: str,
) -> dict[str, Any]:
    params: dict[str, Any] = {}

    params["filename"] = filename

    params = {k: v for k, v in params.items() if v is not UNSET and v is not None}

    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": f"/find_file/generic/experiment_number/{experiment_number}",
        "params": params,
    }

    return _kwargs


def _parse_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Optional[Union[HTTPValidationError, str]]:
    if response.status_code == 200:
        response_200 = cast(str, response.json())
        return response_200
    if response.status_code == 422:
        response_422 = HTTPValidationError.from_dict(response.json())

        return response_422
    if client.raise_on_unexpected_status:
        raise errors.UnexpectedStatus(response.status_code, response.content)
    else:
        return None


def _build_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Response[Union[HTTPValidationError, str]]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    experiment_number: int,
    *,
    client: AuthenticatedClient,
    filename: str,
) -> Response[Union[HTTPValidationError, str]]:
    """Find File Generic Experiment Number

     Return the relative path to the env var CEPH_DIR that leads to the requested file if one exists.

    Args:
        experiment_number (int):
        filename (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[HTTPValidationError, str]]
    """

    kwargs = _get_kwargs(
        experiment_number=experiment_number,
        filename=filename,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    experiment_number: int,
    *,
    client: AuthenticatedClient,
    filename: str,
) -> Optional[Union[HTTPValidationError, str]]:
    """Find File Generic Experiment Number

     Return the relative path to the env var CEPH_DIR that leads to the requested file if one exists.

    Args:
        experiment_number (int):
        filename (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[HTTPValidationError, str]
    """

    return sync_detailed(
        experiment_number=experiment_number,
        client=client,
        filename=filename,
    ).parsed


async def asyncio_detailed(
    experiment_number: int,
    *,
    client: AuthenticatedClient,
    filename: str,
) -> Response[Union[HTTPValidationError, str]]:
    """Find File Generic Experiment Number

     Return the relative path to the env var CEPH_DIR that leads to the requested file if one exists.

    Args:
        experiment_number (int):
        filename (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[HTTPValidationError, str]]
    """

    kwargs = _get_kwargs(
        experiment_number=experiment_number,
        filename=filename,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    experiment_number: int,
    *,
    client: AuthenticatedClient,
    filename: str,
) -> Optional[Union[HTTPValidationError, str]]:
    """Find File Generic Experiment Number

     Return the relative path to the env var CEPH_DIR that leads to the requested file if one exists.

    Args:
        experiment_number (int):
        filename (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[HTTPValidationError, str]
    """

    return (
        await asyncio_detailed(
            experiment_number=experiment_number,
            client=client,
            filename=filename,
        )
    ).parsed

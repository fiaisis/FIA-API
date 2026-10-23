from http import HTTPStatus
from typing import Any, Optional, Union

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.autoreduction_request import AutoreductionRequest
from ...models.autoreduction_response import AutoreductionResponse
from ...models.http_validation_error import HTTPValidationError
from ...types import Response


def _get_kwargs(
    *,
    body: AutoreductionRequest,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}

    _kwargs: dict[str, Any] = {
        "method": "post",
        "url": "/job/autoreduction",
    }

    _kwargs["json"] = body.to_dict()

    headers["Content-Type"] = "application/json"

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Optional[Union[AutoreductionResponse, HTTPValidationError]]:
    if response.status_code == 200:
        response_200 = AutoreductionResponse.from_dict(response.json())

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
) -> Response[Union[AutoreductionResponse, HTTPValidationError]]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    *,
    client: AuthenticatedClient,
    body: AutoreductionRequest,
) -> Response[Union[AutoreductionResponse, HTTPValidationError]]:
    """Create Autoreduction

     Given an AutoreductionRequest, return an AutoreductionResponse containing the job id and the
    autoreduction script

    Args:
        body (AutoreductionRequest): Autoreduction request encompasses all the fields necessary
            for an autoreduction job to be created

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[AutoreductionResponse, HTTPValidationError]]
    """

    kwargs = _get_kwargs(
        body=body,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    *,
    client: AuthenticatedClient,
    body: AutoreductionRequest,
) -> Optional[Union[AutoreductionResponse, HTTPValidationError]]:
    """Create Autoreduction

     Given an AutoreductionRequest, return an AutoreductionResponse containing the job id and the
    autoreduction script

    Args:
        body (AutoreductionRequest): Autoreduction request encompasses all the fields necessary
            for an autoreduction job to be created

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[AutoreductionResponse, HTTPValidationError]
    """

    return sync_detailed(
        client=client,
        body=body,
    ).parsed


async def asyncio_detailed(
    *,
    client: AuthenticatedClient,
    body: AutoreductionRequest,
) -> Response[Union[AutoreductionResponse, HTTPValidationError]]:
    """Create Autoreduction

     Given an AutoreductionRequest, return an AutoreductionResponse containing the job id and the
    autoreduction script

    Args:
        body (AutoreductionRequest): Autoreduction request encompasses all the fields necessary
            for an autoreduction job to be created

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[AutoreductionResponse, HTTPValidationError]]
    """

    kwargs = _get_kwargs(
        body=body,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: AuthenticatedClient,
    body: AutoreductionRequest,
) -> Optional[Union[AutoreductionResponse, HTTPValidationError]]:
    """Create Autoreduction

     Given an AutoreductionRequest, return an AutoreductionResponse containing the job id and the
    autoreduction script

    Args:
        body (AutoreductionRequest): Autoreduction request encompasses all the fields necessary
            for an autoreduction job to be created

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[AutoreductionResponse, HTTPValidationError]
    """

    return (
        await asyncio_detailed(
            client=client,
            body=body,
        )
    ).parsed

from http import HTTPStatus
from typing import Any, Optional, Union

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.http_validation_error import HTTPValidationError
from ...models.job_response import JobResponse
from ...models.partial_job_update_request import PartialJobUpdateRequest
from ...types import Response


def _get_kwargs(
    job_id: int,
    *,
    body: PartialJobUpdateRequest,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}

    _kwargs: dict[str, Any] = {
        "method": "patch",
        "url": f"/job/{job_id}",
    }

    _kwargs["json"] = body.to_dict()

    headers["Content-Type"] = "application/json"

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Optional[Union[HTTPValidationError, JobResponse]]:
    if response.status_code == 200:
        response_200 = JobResponse.from_dict(response.json())

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
) -> Response[Union[HTTPValidationError, JobResponse]]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    job_id: int,
    *,
    client: AuthenticatedClient,
    body: PartialJobUpdateRequest,
) -> Response[Union[HTTPValidationError, JobResponse]]:
    """Update Job

     Safely update the job of the given id with the new details provided. The update is safe as it
    prevents
    retroactive changes of values that should never change

    Args:
        job_id (int):
        body (PartialJobUpdateRequest): Partial Job Update Request encompasses all the safely
            updatable fields on a Job

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[HTTPValidationError, JobResponse]]
    """

    kwargs = _get_kwargs(
        job_id=job_id,
        body=body,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    job_id: int,
    *,
    client: AuthenticatedClient,
    body: PartialJobUpdateRequest,
) -> Optional[Union[HTTPValidationError, JobResponse]]:
    """Update Job

     Safely update the job of the given id with the new details provided. The update is safe as it
    prevents
    retroactive changes of values that should never change

    Args:
        job_id (int):
        body (PartialJobUpdateRequest): Partial Job Update Request encompasses all the safely
            updatable fields on a Job

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[HTTPValidationError, JobResponse]
    """

    return sync_detailed(
        job_id=job_id,
        client=client,
        body=body,
    ).parsed


async def asyncio_detailed(
    job_id: int,
    *,
    client: AuthenticatedClient,
    body: PartialJobUpdateRequest,
) -> Response[Union[HTTPValidationError, JobResponse]]:
    """Update Job

     Safely update the job of the given id with the new details provided. The update is safe as it
    prevents
    retroactive changes of values that should never change

    Args:
        job_id (int):
        body (PartialJobUpdateRequest): Partial Job Update Request encompasses all the safely
            updatable fields on a Job

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[HTTPValidationError, JobResponse]]
    """

    kwargs = _get_kwargs(
        job_id=job_id,
        body=body,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    job_id: int,
    *,
    client: AuthenticatedClient,
    body: PartialJobUpdateRequest,
) -> Optional[Union[HTTPValidationError, JobResponse]]:
    """Update Job

     Safely update the job of the given id with the new details provided. The update is safe as it
    prevents
    retroactive changes of values that should never change

    Args:
        job_id (int):
        body (PartialJobUpdateRequest): Partial Job Update Request encompasses all the safely
            updatable fields on a Job

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[HTTPValidationError, JobResponse]
    """

    return (
        await asyncio_detailed(
            job_id=job_id,
            client=client,
            body=body,
        )
    ).parsed

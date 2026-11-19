from http import HTTPStatus
from typing import Any, Optional, Union

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.count_response import CountResponse
from ...models.http_validation_error import HTTPValidationError
from ...types import UNSET, Response, Unset


def _get_kwargs(
    instrument: str,
    *,
    filters: Union[None, Unset, str] = UNSET,
) -> dict[str, Any]:
    params: dict[str, Any] = {}

    json_filters: Union[None, Unset, str]
    if isinstance(filters, Unset):
        json_filters = UNSET
    else:
        json_filters = filters
    params["filters"] = json_filters

    params = {k: v for k, v in params.items() if v is not UNSET and v is not None}

    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": f"/instrument/{instrument}/jobs/count",
        "params": params,
    }

    return _kwargs


def _parse_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Optional[Union[CountResponse, HTTPValidationError]]:
    if response.status_code == 200:
        response_200 = CountResponse.from_dict(response.json())

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
) -> Response[Union[CountResponse, HTTPValidationError]]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    instrument: str,
    *,
    client: Union[AuthenticatedClient, Client],
    filters: Union[None, Unset, str] = UNSET,
) -> Response[Union[CountResponse, HTTPValidationError]]:
    """Count Jobs For Instrument

     Count jobs for a given instrument.

    Args:
        instrument (str):
        filters (Union[None, Unset, str]): json string of filters

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[CountResponse, HTTPValidationError]]
    """

    kwargs = _get_kwargs(
        instrument=instrument,
        filters=filters,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    instrument: str,
    *,
    client: Union[AuthenticatedClient, Client],
    filters: Union[None, Unset, str] = UNSET,
) -> Optional[Union[CountResponse, HTTPValidationError]]:
    """Count Jobs For Instrument

     Count jobs for a given instrument.

    Args:
        instrument (str):
        filters (Union[None, Unset, str]): json string of filters

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[CountResponse, HTTPValidationError]
    """

    return sync_detailed(
        instrument=instrument,
        client=client,
        filters=filters,
    ).parsed


async def asyncio_detailed(
    instrument: str,
    *,
    client: Union[AuthenticatedClient, Client],
    filters: Union[None, Unset, str] = UNSET,
) -> Response[Union[CountResponse, HTTPValidationError]]:
    """Count Jobs For Instrument

     Count jobs for a given instrument.

    Args:
        instrument (str):
        filters (Union[None, Unset, str]): json string of filters

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[CountResponse, HTTPValidationError]]
    """

    kwargs = _get_kwargs(
        instrument=instrument,
        filters=filters,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    instrument: str,
    *,
    client: Union[AuthenticatedClient, Client],
    filters: Union[None, Unset, str] = UNSET,
) -> Optional[Union[CountResponse, HTTPValidationError]]:
    """Count Jobs For Instrument

     Count jobs for a given instrument.

    Args:
        instrument (str):
        filters (Union[None, Unset, str]): json string of filters

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[CountResponse, HTTPValidationError]
    """

    return (
        await asyncio_detailed(
            instrument=instrument,
            client=client,
            filters=filters,
        )
    ).parsed

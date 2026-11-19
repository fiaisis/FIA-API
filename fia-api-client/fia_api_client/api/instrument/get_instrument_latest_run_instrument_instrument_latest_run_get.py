from http import HTTPStatus
from typing import Any, Optional, Union

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.get_instrument_latest_run_instrument_instrument_latest_run_get_response_get_instrument_latest_run_instrument_instrument_latest_run_get import (
    GetInstrumentLatestRunInstrumentInstrumentLatestRunGetResponseGetInstrumentLatestRunInstrumentInstrumentLatestRunGet,
)
from ...models.http_validation_error import HTTPValidationError
from ...types import Response


def _get_kwargs(
    instrument: str,
) -> dict[str, Any]:
    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": f"/instrument/{instrument}/latest-run",
    }

    return _kwargs


def _parse_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Optional[
    Union[
        GetInstrumentLatestRunInstrumentInstrumentLatestRunGetResponseGetInstrumentLatestRunInstrumentInstrumentLatestRunGet,
        HTTPValidationError,
    ]
]:
    if response.status_code == 200:
        response_200 = GetInstrumentLatestRunInstrumentInstrumentLatestRunGetResponseGetInstrumentLatestRunInstrumentInstrumentLatestRunGet.from_dict(
            response.json()
        )

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
) -> Response[
    Union[
        GetInstrumentLatestRunInstrumentInstrumentLatestRunGetResponseGetInstrumentLatestRunInstrumentInstrumentLatestRunGet,
        HTTPValidationError,
    ]
]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    instrument: str,
    *,
    client: AuthenticatedClient,
) -> Response[
    Union[
        GetInstrumentLatestRunInstrumentInstrumentLatestRunGetResponseGetInstrumentLatestRunInstrumentInstrumentLatestRunGet,
        HTTPValidationError,
    ]
]:
    """Get Instrument Latest Run

     Return the latest run for the given instrument

    Args:
        instrument (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[GetInstrumentLatestRunInstrumentInstrumentLatestRunGetResponseGetInstrumentLatestRunInstrumentInstrumentLatestRunGet, HTTPValidationError]]
    """

    kwargs = _get_kwargs(
        instrument=instrument,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    instrument: str,
    *,
    client: AuthenticatedClient,
) -> Optional[
    Union[
        GetInstrumentLatestRunInstrumentInstrumentLatestRunGetResponseGetInstrumentLatestRunInstrumentInstrumentLatestRunGet,
        HTTPValidationError,
    ]
]:
    """Get Instrument Latest Run

     Return the latest run for the given instrument

    Args:
        instrument (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[GetInstrumentLatestRunInstrumentInstrumentLatestRunGetResponseGetInstrumentLatestRunInstrumentInstrumentLatestRunGet, HTTPValidationError]
    """

    return sync_detailed(
        instrument=instrument,
        client=client,
    ).parsed


async def asyncio_detailed(
    instrument: str,
    *,
    client: AuthenticatedClient,
) -> Response[
    Union[
        GetInstrumentLatestRunInstrumentInstrumentLatestRunGetResponseGetInstrumentLatestRunInstrumentInstrumentLatestRunGet,
        HTTPValidationError,
    ]
]:
    """Get Instrument Latest Run

     Return the latest run for the given instrument

    Args:
        instrument (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[GetInstrumentLatestRunInstrumentInstrumentLatestRunGetResponseGetInstrumentLatestRunInstrumentInstrumentLatestRunGet, HTTPValidationError]]
    """

    kwargs = _get_kwargs(
        instrument=instrument,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    instrument: str,
    *,
    client: AuthenticatedClient,
) -> Optional[
    Union[
        GetInstrumentLatestRunInstrumentInstrumentLatestRunGetResponseGetInstrumentLatestRunInstrumentInstrumentLatestRunGet,
        HTTPValidationError,
    ]
]:
    """Get Instrument Latest Run

     Return the latest run for the given instrument

    Args:
        instrument (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[GetInstrumentLatestRunInstrumentInstrumentLatestRunGetResponseGetInstrumentLatestRunInstrumentInstrumentLatestRunGet, HTTPValidationError]
    """

    return (
        await asyncio_detailed(
            instrument=instrument,
            client=client,
        )
    ).parsed

from http import HTTPStatus
from typing import Any, Optional, Union, cast

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.get_instrument_script_live_data_instrument_script_get_instrument import (
    GetInstrumentScriptLiveDataInstrumentScriptGetInstrument,
)
from ...models.http_validation_error import HTTPValidationError
from ...types import Response


def _get_kwargs(
    instrument: GetInstrumentScriptLiveDataInstrumentScriptGetInstrument,
) -> dict[str, Any]:
    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": f"/live-data/{instrument}/script",
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
    instrument: GetInstrumentScriptLiveDataInstrumentScriptGetInstrument,
    *,
    client: Union[AuthenticatedClient, Client],
) -> Response[Union[HTTPValidationError, str]]:
    """Get Instrument Script

     Given an instrument string, return the live data script for that instrument

    Args:
        instrument (GetInstrumentScriptLiveDataInstrumentScriptGetInstrument):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[HTTPValidationError, str]]
    """

    kwargs = _get_kwargs(
        instrument=instrument,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    instrument: GetInstrumentScriptLiveDataInstrumentScriptGetInstrument,
    *,
    client: Union[AuthenticatedClient, Client],
) -> Optional[Union[HTTPValidationError, str]]:
    """Get Instrument Script

     Given an instrument string, return the live data script for that instrument

    Args:
        instrument (GetInstrumentScriptLiveDataInstrumentScriptGetInstrument):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[HTTPValidationError, str]
    """

    return sync_detailed(
        instrument=instrument,
        client=client,
    ).parsed


async def asyncio_detailed(
    instrument: GetInstrumentScriptLiveDataInstrumentScriptGetInstrument,
    *,
    client: Union[AuthenticatedClient, Client],
) -> Response[Union[HTTPValidationError, str]]:
    """Get Instrument Script

     Given an instrument string, return the live data script for that instrument

    Args:
        instrument (GetInstrumentScriptLiveDataInstrumentScriptGetInstrument):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[HTTPValidationError, str]]
    """

    kwargs = _get_kwargs(
        instrument=instrument,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    instrument: GetInstrumentScriptLiveDataInstrumentScriptGetInstrument,
    *,
    client: Union[AuthenticatedClient, Client],
) -> Optional[Union[HTTPValidationError, str]]:
    """Get Instrument Script

     Given an instrument string, return the live data script for that instrument

    Args:
        instrument (GetInstrumentScriptLiveDataInstrumentScriptGetInstrument):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[HTTPValidationError, str]
    """

    return (
        await asyncio_detailed(
            instrument=instrument,
            client=client,
        )
    ).parsed

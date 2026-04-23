from http import HTTPStatus
from typing import Any, Literal, Optional, Union, cast

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.http_validation_error import HTTPValidationError
from ...models.live_data_script_update_request import LiveDataScriptUpdateRequest
from ...models.update_instrument_script_live_data_instrument_script_put_instrument import (
    UpdateInstrumentScriptLiveDataInstrumentScriptPutInstrument,
)
from ...types import Response


def _get_kwargs(
    instrument: UpdateInstrumentScriptLiveDataInstrumentScriptPutInstrument,
    *,
    body: LiveDataScriptUpdateRequest,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}

    _kwargs: dict[str, Any] = {
        "method": "put",
        "url": f"/live-data/{instrument}/script",
    }

    _kwargs["json"] = body.to_dict()

    headers["Content-Type"] = "application/json"

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Optional[Union[HTTPValidationError, Literal["ok"]]]:
    if response.status_code == 200:
        response_200 = cast(Literal["ok"], response.json())
        if response_200 != "ok":
            raise ValueError(f"response_200 must match const 'ok', got '{response_200}'")
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
) -> Response[Union[HTTPValidationError, Literal["ok"]]]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    instrument: UpdateInstrumentScriptLiveDataInstrumentScriptPutInstrument,
    *,
    client: AuthenticatedClient,
    body: LiveDataScriptUpdateRequest,
) -> Response[Union[HTTPValidationError, Literal["ok"]]]:
    """Update Instrument Script

     Given an instrument string and a script request, update the live data script for that instrument

    Args:
        instrument (UpdateInstrumentScriptLiveDataInstrumentScriptPutInstrument):
        body (LiveDataScriptUpdateRequest): Script Update Request for live data

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[HTTPValidationError, Literal['ok']]]
    """

    kwargs = _get_kwargs(
        instrument=instrument,
        body=body,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    instrument: UpdateInstrumentScriptLiveDataInstrumentScriptPutInstrument,
    *,
    client: AuthenticatedClient,
    body: LiveDataScriptUpdateRequest,
) -> Optional[Union[HTTPValidationError, Literal["ok"]]]:
    """Update Instrument Script

     Given an instrument string and a script request, update the live data script for that instrument

    Args:
        instrument (UpdateInstrumentScriptLiveDataInstrumentScriptPutInstrument):
        body (LiveDataScriptUpdateRequest): Script Update Request for live data

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[HTTPValidationError, Literal['ok']]
    """

    return sync_detailed(
        instrument=instrument,
        client=client,
        body=body,
    ).parsed


async def asyncio_detailed(
    instrument: UpdateInstrumentScriptLiveDataInstrumentScriptPutInstrument,
    *,
    client: AuthenticatedClient,
    body: LiveDataScriptUpdateRequest,
) -> Response[Union[HTTPValidationError, Literal["ok"]]]:
    """Update Instrument Script

     Given an instrument string and a script request, update the live data script for that instrument

    Args:
        instrument (UpdateInstrumentScriptLiveDataInstrumentScriptPutInstrument):
        body (LiveDataScriptUpdateRequest): Script Update Request for live data

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[HTTPValidationError, Literal['ok']]]
    """

    kwargs = _get_kwargs(
        instrument=instrument,
        body=body,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    instrument: UpdateInstrumentScriptLiveDataInstrumentScriptPutInstrument,
    *,
    client: AuthenticatedClient,
    body: LiveDataScriptUpdateRequest,
) -> Optional[Union[HTTPValidationError, Literal["ok"]]]:
    """Update Instrument Script

     Given an instrument string and a script request, update the live data script for that instrument

    Args:
        instrument (UpdateInstrumentScriptLiveDataInstrumentScriptPutInstrument):
        body (LiveDataScriptUpdateRequest): Script Update Request for live data

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[HTTPValidationError, Literal['ok']]
    """

    return (
        await asyncio_detailed(
            instrument=instrument,
            client=client,
            body=body,
        )
    ).parsed

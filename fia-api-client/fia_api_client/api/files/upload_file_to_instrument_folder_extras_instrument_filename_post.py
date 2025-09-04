from http import HTTPStatus
from typing import Any, Optional, Union, cast

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.body_upload_file_to_instrument_folder_extras_instrument_filename_post import (
    BodyUploadFileToInstrumentFolderExtrasInstrumentFilenamePost,
)
from ...models.http_validation_error import HTTPValidationError
from ...models.upload_file_to_instrument_folder_extras_instrument_filename_post_instrument import (
    UploadFileToInstrumentFolderExtrasInstrumentFilenamePostInstrument,
)
from ...types import Response


def _get_kwargs(
    instrument: UploadFileToInstrumentFolderExtrasInstrumentFilenamePostInstrument,
    filename: str,
    *,
    body: BodyUploadFileToInstrumentFolderExtrasInstrumentFilenamePost,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}

    _kwargs: dict[str, Any] = {
        "method": "post",
        "url": f"/extras/{instrument}/{filename}",
    }

    _kwargs["files"] = body.to_multipart()

    _kwargs["headers"] = headers
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
    instrument: UploadFileToInstrumentFolderExtrasInstrumentFilenamePostInstrument,
    filename: str,
    *,
    client: AuthenticatedClient,
    body: BodyUploadFileToInstrumentFolderExtrasInstrumentFilenamePost,
) -> Response[Union[HTTPValidationError, str]]:
    """Upload File To Instrument Folder

     Uploads a file to the instrument folder, prevents access to folder any other
    directory other than extras and its sub folders.

    Args:
        instrument (UploadFileToInstrumentFolderExtrasInstrumentFilenamePostInstrument):
        filename (str):
        body (BodyUploadFileToInstrumentFolderExtrasInstrumentFilenamePost):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[HTTPValidationError, str]]
    """

    kwargs = _get_kwargs(
        instrument=instrument,
        filename=filename,
        body=body,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    instrument: UploadFileToInstrumentFolderExtrasInstrumentFilenamePostInstrument,
    filename: str,
    *,
    client: AuthenticatedClient,
    body: BodyUploadFileToInstrumentFolderExtrasInstrumentFilenamePost,
) -> Optional[Union[HTTPValidationError, str]]:
    """Upload File To Instrument Folder

     Uploads a file to the instrument folder, prevents access to folder any other
    directory other than extras and its sub folders.

    Args:
        instrument (UploadFileToInstrumentFolderExtrasInstrumentFilenamePostInstrument):
        filename (str):
        body (BodyUploadFileToInstrumentFolderExtrasInstrumentFilenamePost):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[HTTPValidationError, str]
    """

    return sync_detailed(
        instrument=instrument,
        filename=filename,
        client=client,
        body=body,
    ).parsed


async def asyncio_detailed(
    instrument: UploadFileToInstrumentFolderExtrasInstrumentFilenamePostInstrument,
    filename: str,
    *,
    client: AuthenticatedClient,
    body: BodyUploadFileToInstrumentFolderExtrasInstrumentFilenamePost,
) -> Response[Union[HTTPValidationError, str]]:
    """Upload File To Instrument Folder

     Uploads a file to the instrument folder, prevents access to folder any other
    directory other than extras and its sub folders.

    Args:
        instrument (UploadFileToInstrumentFolderExtrasInstrumentFilenamePostInstrument):
        filename (str):
        body (BodyUploadFileToInstrumentFolderExtrasInstrumentFilenamePost):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[HTTPValidationError, str]]
    """

    kwargs = _get_kwargs(
        instrument=instrument,
        filename=filename,
        body=body,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    instrument: UploadFileToInstrumentFolderExtrasInstrumentFilenamePostInstrument,
    filename: str,
    *,
    client: AuthenticatedClient,
    body: BodyUploadFileToInstrumentFolderExtrasInstrumentFilenamePost,
) -> Optional[Union[HTTPValidationError, str]]:
    """Upload File To Instrument Folder

     Uploads a file to the instrument folder, prevents access to folder any other
    directory other than extras and its sub folders.

    Args:
        instrument (UploadFileToInstrumentFolderExtrasInstrumentFilenamePostInstrument):
        filename (str):
        body (BodyUploadFileToInstrumentFolderExtrasInstrumentFilenamePost):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[HTTPValidationError, str]
    """

    return (
        await asyncio_detailed(
            instrument=instrument,
            filename=filename,
            client=client,
            body=body,
        )
    ).parsed

from http import HTTPStatus
from typing import Any, Optional, Union

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.get_jobs_jobs_get_order_by import GetJobsJobsGetOrderBy
from ...models.get_jobs_jobs_get_order_direction import GetJobsJobsGetOrderDirection
from ...models.http_validation_error import HTTPValidationError
from ...models.job_response import JobResponse
from ...models.job_with_run_response import JobWithRunResponse
from ...types import UNSET, Response, Unset


def _get_kwargs(
    *,
    limit: Union[Unset, int] = 0,
    offset: Union[Unset, int] = 0,
    order_by: Union[Unset, GetJobsJobsGetOrderBy] = GetJobsJobsGetOrderBy.START,
    order_direction: Union[Unset, GetJobsJobsGetOrderDirection] = GetJobsJobsGetOrderDirection.DESC,
    include_run: Union[Unset, bool] = False,
    filters: Union[None, Unset, str] = UNSET,
    as_user: Union[Unset, bool] = False,
) -> dict[str, Any]:
    params: dict[str, Any] = {}

    params["limit"] = limit

    params["offset"] = offset

    json_order_by: Union[Unset, str] = UNSET
    if not isinstance(order_by, Unset):
        json_order_by = order_by.value

    params["order_by"] = json_order_by

    json_order_direction: Union[Unset, str] = UNSET
    if not isinstance(order_direction, Unset):
        json_order_direction = order_direction.value

    params["order_direction"] = json_order_direction

    params["include_run"] = include_run

    json_filters: Union[None, Unset, str]
    if isinstance(filters, Unset):
        json_filters = UNSET
    else:
        json_filters = filters
    params["filters"] = json_filters

    params["as_user"] = as_user

    params = {k: v for k, v in params.items() if v is not UNSET and v is not None}

    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": "/jobs",
        "params": params,
    }

    return _kwargs


def _parse_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Optional[Union[HTTPValidationError, Union[list["JobResponse"], list["JobWithRunResponse"]]]]:
    if response.status_code == 200:

        def _parse_response_200(data: object) -> Union[list["JobResponse"], list["JobWithRunResponse"]]:
            try:
                if not isinstance(data, list):
                    raise TypeError()
                response_200_type_0 = []
                _response_200_type_0 = data
                for response_200_type_0_item_data in _response_200_type_0:
                    response_200_type_0_item = JobResponse.from_dict(response_200_type_0_item_data)

                    response_200_type_0.append(response_200_type_0_item)

                return response_200_type_0
            except:  # noqa: E722
                pass
            if not isinstance(data, list):
                raise TypeError()
            response_200_type_1 = []
            _response_200_type_1 = data
            for response_200_type_1_item_data in _response_200_type_1:
                response_200_type_1_item = JobWithRunResponse.from_dict(response_200_type_1_item_data)

                response_200_type_1.append(response_200_type_1_item)

            return response_200_type_1

        response_200 = _parse_response_200(response.json())

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
) -> Response[Union[HTTPValidationError, Union[list["JobResponse"], list["JobWithRunResponse"]]]]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    *,
    client: AuthenticatedClient,
    limit: Union[Unset, int] = 0,
    offset: Union[Unset, int] = 0,
    order_by: Union[Unset, GetJobsJobsGetOrderBy] = GetJobsJobsGetOrderBy.START,
    order_direction: Union[Unset, GetJobsJobsGetOrderDirection] = GetJobsJobsGetOrderDirection.DESC,
    include_run: Union[Unset, bool] = False,
    filters: Union[None, Unset, str] = UNSET,
    as_user: Union[Unset, bool] = False,
) -> Response[Union[HTTPValidationError, Union[list["JobResponse"], list["JobWithRunResponse"]]]]:
    """Get Jobs

     Retrieve all jobs.

    Args:
        limit (Union[Unset, int]):  Default: 0.
        offset (Union[Unset, int]):  Default: 0.
        order_by (Union[Unset, GetJobsJobsGetOrderBy]):  Default: GetJobsJobsGetOrderBy.START.
        order_direction (Union[Unset, GetJobsJobsGetOrderDirection]):  Default:
            GetJobsJobsGetOrderDirection.DESC.
        include_run (Union[Unset, bool]):  Default: False.
        filters (Union[None, Unset, str]): json string of filters
        as_user (Union[Unset, bool]):  Default: False.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[HTTPValidationError, Union[list['JobResponse'], list['JobWithRunResponse']]]]
    """

    kwargs = _get_kwargs(
        limit=limit,
        offset=offset,
        order_by=order_by,
        order_direction=order_direction,
        include_run=include_run,
        filters=filters,
        as_user=as_user,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    *,
    client: AuthenticatedClient,
    limit: Union[Unset, int] = 0,
    offset: Union[Unset, int] = 0,
    order_by: Union[Unset, GetJobsJobsGetOrderBy] = GetJobsJobsGetOrderBy.START,
    order_direction: Union[Unset, GetJobsJobsGetOrderDirection] = GetJobsJobsGetOrderDirection.DESC,
    include_run: Union[Unset, bool] = False,
    filters: Union[None, Unset, str] = UNSET,
    as_user: Union[Unset, bool] = False,
) -> Optional[Union[HTTPValidationError, Union[list["JobResponse"], list["JobWithRunResponse"]]]]:
    """Get Jobs

     Retrieve all jobs.

    Args:
        limit (Union[Unset, int]):  Default: 0.
        offset (Union[Unset, int]):  Default: 0.
        order_by (Union[Unset, GetJobsJobsGetOrderBy]):  Default: GetJobsJobsGetOrderBy.START.
        order_direction (Union[Unset, GetJobsJobsGetOrderDirection]):  Default:
            GetJobsJobsGetOrderDirection.DESC.
        include_run (Union[Unset, bool]):  Default: False.
        filters (Union[None, Unset, str]): json string of filters
        as_user (Union[Unset, bool]):  Default: False.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[HTTPValidationError, Union[list['JobResponse'], list['JobWithRunResponse']]]
    """

    return sync_detailed(
        client=client,
        limit=limit,
        offset=offset,
        order_by=order_by,
        order_direction=order_direction,
        include_run=include_run,
        filters=filters,
        as_user=as_user,
    ).parsed


async def asyncio_detailed(
    *,
    client: AuthenticatedClient,
    limit: Union[Unset, int] = 0,
    offset: Union[Unset, int] = 0,
    order_by: Union[Unset, GetJobsJobsGetOrderBy] = GetJobsJobsGetOrderBy.START,
    order_direction: Union[Unset, GetJobsJobsGetOrderDirection] = GetJobsJobsGetOrderDirection.DESC,
    include_run: Union[Unset, bool] = False,
    filters: Union[None, Unset, str] = UNSET,
    as_user: Union[Unset, bool] = False,
) -> Response[Union[HTTPValidationError, Union[list["JobResponse"], list["JobWithRunResponse"]]]]:
    """Get Jobs

     Retrieve all jobs.

    Args:
        limit (Union[Unset, int]):  Default: 0.
        offset (Union[Unset, int]):  Default: 0.
        order_by (Union[Unset, GetJobsJobsGetOrderBy]):  Default: GetJobsJobsGetOrderBy.START.
        order_direction (Union[Unset, GetJobsJobsGetOrderDirection]):  Default:
            GetJobsJobsGetOrderDirection.DESC.
        include_run (Union[Unset, bool]):  Default: False.
        filters (Union[None, Unset, str]): json string of filters
        as_user (Union[Unset, bool]):  Default: False.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[HTTPValidationError, Union[list['JobResponse'], list['JobWithRunResponse']]]]
    """

    kwargs = _get_kwargs(
        limit=limit,
        offset=offset,
        order_by=order_by,
        order_direction=order_direction,
        include_run=include_run,
        filters=filters,
        as_user=as_user,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: AuthenticatedClient,
    limit: Union[Unset, int] = 0,
    offset: Union[Unset, int] = 0,
    order_by: Union[Unset, GetJobsJobsGetOrderBy] = GetJobsJobsGetOrderBy.START,
    order_direction: Union[Unset, GetJobsJobsGetOrderDirection] = GetJobsJobsGetOrderDirection.DESC,
    include_run: Union[Unset, bool] = False,
    filters: Union[None, Unset, str] = UNSET,
    as_user: Union[Unset, bool] = False,
) -> Optional[Union[HTTPValidationError, Union[list["JobResponse"], list["JobWithRunResponse"]]]]:
    """Get Jobs

     Retrieve all jobs.

    Args:
        limit (Union[Unset, int]):  Default: 0.
        offset (Union[Unset, int]):  Default: 0.
        order_by (Union[Unset, GetJobsJobsGetOrderBy]):  Default: GetJobsJobsGetOrderBy.START.
        order_direction (Union[Unset, GetJobsJobsGetOrderDirection]):  Default:
            GetJobsJobsGetOrderDirection.DESC.
        include_run (Union[Unset, bool]):  Default: False.
        filters (Union[None, Unset, str]): json string of filters
        as_user (Union[Unset, bool]):  Default: False.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[HTTPValidationError, Union[list['JobResponse'], list['JobWithRunResponse']]]
    """

    return (
        await asyncio_detailed(
            client=client,
            limit=limit,
            offset=offset,
            order_by=order_by,
            order_direction=order_direction,
            include_run=include_run,
            filters=filters,
            as_user=as_user,
        )
    ).parsed

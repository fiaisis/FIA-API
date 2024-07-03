"""
Service Layer for reductions
"""

from collections.abc import Sequence
from typing import Literal

from fia_api.core.auth.experiments import get_experiments_for_user_number
from fia_api.core.exceptions import AuthenticationError, MissingRecordError
from fia_api.core.model import Reduction
from fia_api.core.repositories import Repo
from fia_api.core.specifications.reduction import ReductionSpecification

OrderField = Literal[
    "reduction_start",
    "reduction_end",
    "reduction_state",
    "id",
    "run_start",
    "run_end",
    "reduction_outputs",
    "experiment_number",
    "experiment_title",
    "filename",
]

_REPO: Repo[Reduction] = Repo()


def get_reductions_by_instrument(
    instrument: str,
    limit: int = 0,
    offset: int = 0,
    order_by: OrderField = "reduction_start",
    order_direction: Literal["asc", "desc"] = "desc",
    user_number: int | None = None,
) -> Sequence[Reduction]:
    """
    Given an instrument name return a sequence of reductions for that instrument. Optionally providing a limit and
    offset to be applied to the sequence
    :param instrument: (str) - The instrument to get by
    :param limit: (int) - the maximum number of results to be allowed in the sequence
    :param offset: (int) - the number of reductions to offset the sequence from the entire reduction set
    :param order_direction: (str) Direction to der by "asc" | "desc"
    :param order_by: (str) Field to order by.
    :return: Sequence of Reductions for an instrument
    """

    return _REPO.find(
        ReductionSpecification().by_instrument(
            instrument=instrument,
            limit=limit,
            offset=offset,
            order_by=order_by,
            order_direction=order_direction,
            user_number=user_number,
        )
    )


def get_all_reductions(
    limit: int = 0,
    offset: int = 0,
    order_by: OrderField = "reduction_start",
    order_direction: Literal["asc", "desc"] = "desc",
    user_number: int | None = None,
) -> Sequence[Reduction]:
    """
    Get all reductions, if a user number is provided then only the reductions that user has permission for will be
    provided.
    :param user_number:  Optional user number to filter with
    :param limit: (int) - the maximum number of results to be allowed in the sequence
    :param offset: (int) - the number of reductions to offset the sequence from the entire reduction set
    :param order_direction: (str) Direction to der by "asc" | "desc"
    :param order_by: (str) Field to order by.
    :return: A Sequence of Reductions
    """
    if user_number is None:
        return _REPO.find(
            ReductionSpecification().all(limit=limit, offset=offset, order_by=order_by, order_direction=order_direction)
        )
    experiment_numbers = get_experiments_for_user_number(user_number)
    return _REPO.find(
        ReductionSpecification().by_experiment_numbers(
            experiment_numbers, limit=limit, offset=offset, order_direction=order_direction, order_by=order_by
        )
    )


def get_reduction_by_id(reduction_id: int, user_number: int | None = None) -> Reduction:
    """
    Given an ID return the reduction with that ID
    :param reduction_id: The id of the reduction to search for
    :return: The reduction
    :raises: MissingRecordError when no reduction for that ID is found
    """
    reduction = _REPO.find_one(ReductionSpecification().by_id(reduction_id))
    if reduction is None:
        raise MissingRecordError(f"No Reduction for id {reduction_id}")

    if user_number:
        experiments = get_experiments_for_user_number(user_number)
        if not any(run.experiment_number in experiments for run in reduction.runs):
            raise AuthenticationError("User does not have permission for run")

    return reduction


def count_reductions_by_instrument(instrument: str) -> int:
    """
    Given an instrument name, count the reductions for that instrument
    :param instrument: Instrument to count from
    :return: Number of reductions
    """
    return _REPO.count(ReductionSpecification().by_instrument(instrument=instrument))


def count_reductions() -> int:
    """
    Count the total number of reductions
    :return: (int) number of reductions
    """
    return _REPO.count(ReductionSpecification().all())

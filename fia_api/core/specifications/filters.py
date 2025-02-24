"""
Module providing filter implementations for modifying specifications in database queries. Filters are
used to apply conditions in a modular and reusable way, leveraging specific fields from the data models.
"""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from collections.abc import Mapping
from http import HTTPStatus
from typing import Any

from db.data_models import Instrument, Job, JobOwner, Run
from fastapi import HTTPException

from fia_api.core.specifications.base import Specification, T

logger = logging.getLogger(__name__)


class Filter(ABC):
    """
    Abstract base class for creating filters to apply conditions to database query specifications.

    Subclasses must implement the `apply` method, which defines the specific condition to be
    applied to the provided specification.
    """

    def __init__(self, value: Any):
        self.value = value

    @abstractmethod
    def apply(self, specification: Specification[T]) -> Specification[T]:
        """Apply the filter to the given specification"""
        pass


class InstrumentInFilter(Filter):
    """Filter implementation that checks if instrument names are included in the query."""

    def apply(self, specification: Specification[T]) -> Specification[T]:
        specification.value = specification.value.where(Instrument.instrument_name.in_(self.value))
        return specification


class ExperimentNumberInFilter(Filter):
    """Filter implementation that checks if experiment numbers are included in the query by joining related tables."""

    def apply(self, specification: Specification[T]) -> Specification[T]:
        specification.value = specification.value.where(JobOwner.experiment_number.in_(self.value))
        logger.info(specification.value)
        return specification


class JobStateFilter(Filter):
    """Filter implementation that checks if job states match the specified value in the query."""

    def apply(self, specification: Specification[T]) -> Specification[T]:
        specification.value = specification.value.where(Job.state.in_(self.value))
        return specification


class JobTypeFilter(Filter):
    """Filter implementation that checks if job types match the specified value in the query."""

    def apply(self, specification: Specification[T]) -> Specification[T]:
        specification.value = specification.value.where(Job.job_type == self.value)
        return specification


class TitleFilter(Filter):
    """Filter implementation that searches for entries with titles matching the specified value using ilike."""

    def apply(self, specification: Specification[T]) -> Specification[T]:
        specification.value = specification.value.where(Run.title.icontains(self.value))
        return specification


class ExperimentNumberBeforeFilter(Filter):
    """Filter implementation that retrieves entries with experiment numbers less than the specified value."""

    def apply(self, specification: Specification[T]) -> Specification[T]:
        specification.value = specification.value.where(JobOwner.experiment_number <= self.value)
        return specification


class ExperimentNumberAfterFilter(Filter):
    """Filter implementation that retrieves entries with experiment numbers greater than the specified value."""

    def apply(self, specification: Specification[T]) -> Specification[T]:
        specification.value = specification.value.where(JobOwner.experiment_number >= self.value)
        return specification


class FilenameFilter(Filter):
    """Filter implementation that searches for entries with filenames matching the specified value using ilike."""

    def apply(self, specification: Specification[T]) -> Specification[T]:
        specification.value = specification.value.where(Run.filename.icontains(self.value))
        return specification


class JobStartBeforeFilter(Filter):
    """Filter implementation that retrieves entries where job start is before the specified value."""

    def apply(self, specification: Specification[T]) -> Specification[T]:
        specification.value = specification.value.where(Job.start < self.value)
        return specification


class JobStartAfterFilter(Filter):
    """Filter implementation that retrieves entries where job start is after the specified value."""

    def apply(self, specification: Specification[T]) -> Specification[T]:
        specification.value = specification.value.where(Job.start > self.value)
        return specification


class RunStartBeforeFilter(Filter):
    """Filter implementation that retrieves entries where run start is before the specified value."""

    def apply(self, specification: Specification[T]) -> Specification[T]:
        specification.value = specification.value.where(Run.run_start < self.value)
        return specification


class RunStartAfterFilter(Filter):
    """Filter implementation that retrieves entries where run start is after the specified value."""

    def apply(self, specification: Specification[T]) -> Specification[T]:
        specification.value = specification.value.where(Run.run_start > self.value)
        return specification


class JobEndBeforeFilter(Filter):
    """Filter implementation that retrieves entries where job end is before the specified value."""

    def apply(self, specification: Specification[T]) -> Specification[T]:
        specification.value = specification.value.where(Job.end < self.value)
        return specification


class JobEndAfterFilter(Filter):
    """Filter implementation that retrieves entries where job end is after the specified value."""

    def apply(self, specification: Specification[T]) -> Specification[T]:
        specification.value = specification.value.where(Job.end > self.value)
        return specification


class RunEndBeforeFilter(Filter):
    """Filter implementation that retrieves entries where run end is before the specified value."""

    def apply(self, specification: Specification[T]) -> Specification[T]:
        specification.value = specification.value.where(Run.run_end < self.value)
        return specification


class RunEndAfterFilter(Filter):
    """Filter implementation that retrieves entries where run end is after the specified value."""

    def apply(self, specification: Specification[T]) -> Specification[T]:
        specification.value = specification.value.where(Run.run_end > self.value)
        return specification


def get_filter(key: str, value: Any) -> Filter:  # noqa: C901, PLR0911, PLR0912
    """
    Create and return a filter instance based on the given key and value.

    :param key: The key identifying the filter type (e.g., "instrument_in", "job_state", "job_type").
    :param value: The value to initialize the filter with, specific to the filter type.
    :return: A specific filter instance based on the provided key.
    :raises HTTPException: If the key does not match any known filter type.
    """
    match key:
        case "instrument_in":
            return InstrumentInFilter(value)
        case "job_state_in":
            return JobStateFilter(value)
        case "job_type":
            return JobTypeFilter(value)
        case "experiment_number_in":
            return ExperimentNumberInFilter(value)
        case "title":
            return TitleFilter(value)
        case "filename":
            return FilenameFilter(value)
        case "job_start_before":
            return JobStartBeforeFilter(value)
        case "job_start_after":
            return JobStartAfterFilter(value)
        case "run_start_before":
            return RunStartBeforeFilter(value)
        case "run_start_after":
            return RunStartAfterFilter(value)
        case "job_end_before":
            return JobEndBeforeFilter(value)
        case "job_end_after":
            return JobEndAfterFilter(value)
        case "run_end_before":
            return RunEndBeforeFilter(value)
        case "run_end_after":
            return RunEndAfterFilter(value)
        case "experiment_number_before":
            return ExperimentNumberBeforeFilter(value)
        case "experiment_number_after":
            return ExperimentNumberAfterFilter(value)
        case _:
            raise HTTPException(status_code=HTTPStatus.BAD_REQUEST, detail="bad filter provided")


def apply_filters_to_spec(filters: Mapping[str, Any], spec: Specification[T]) -> Specification[T]:
    """
    Apply multiple filters to a given specification.
    :param filters: Filter Mapping
    :param spec: An instance of `Specification` that the filters will be applied to.
    :return: A modified `Specification` instance with all filters applied in order.
    """
    for key, value in filters.items():
        spec = get_filter(key, value).apply(spec)
    return spec

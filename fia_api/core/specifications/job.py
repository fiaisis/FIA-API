"""
Module defining specifications for querying Job entities within the FIA API.

It includes the JobSpecification class, which facilitates the construction of complex queries
for fetching Job entities based on various criteria such as instrument name, experiment number,
and ordering preferences.
"""

# The limit and offsets in specifications will incorrectly flag as unused. They are used when they are intercepted by
# the paginate decorator
from __future__ import annotations

from typing import Literal

from db.data_models import Instrument, Job, JobOwner, Run
from sqlalchemy import and_, or_

from fia_api.core.auth.experiments import get_experiments_for_user_number
from fia_api.core.specifications.base import Specification, apply_ordering, paginate

JobOrderField = Literal["start", "end", "state", "id", "outputs"]
RunOrderField = Literal["run_start", "run_end", "experiment_number", "experiment_title", "filename"]
JointRunJobOrderField = RunOrderField | JobOrderField


class JobSpecification(Specification[Job]):
    """
    A specification class for constructing queries to fetch Job entities.

    This class supports filtering and ordering of jobs based on attributes of both
    the Job and Run entities, including support for joint attributes.
    """

    @property
    def model(self) -> type[Job]:
        return Job

    def _apply_ordering(self, order_by: JointRunJobOrderField, order_direction: Literal["asc", "desc"]) -> None:
        match order_by:
            case "filename":
                self.value = (
                    self.value.order_by(Run.filename.desc())
                    if order_direction == "desc"
                    else self.value.order_by(Run.filename.asc())
                )
            case "run_start":
                self.value = (
                    self.value.order_by(Run.run_start.desc())
                    if order_direction == "desc"
                    else self.value.order_by(Run.run_start.asc())
                )
            case "run_end":
                self.value = (
                    self.value.order_by(Run.run_end.desc())
                    if order_direction == "desc"
                    else self.value.order_by(Run.run_end.asc())
                )
            case "experiment_number":
                self.value = self.value.join(JobOwner)
                self.value = (
                    self.value.order_by(JobOwner.experiment_number.desc())
                    if order_direction == "desc"
                    else self.value.order_by(JobOwner.experiment_number.asc())
                )
            case "experiment_title":
                self.value = (
                    self.value.order_by(Run.title.desc())
                    if order_direction == "desc"
                    else self.value.order_by(Run.title.asc())
                )
            case _:
                self.value = apply_ordering(self.value, self.model, order_by, order_direction)

    @paginate
    def by_experiment_numbers(
        self,
        experiment_numbers: list[int],
        limit: int | None = None,
        offset: int | None = None,
        order_by: JointRunJobOrderField = "id",
        order_direction: Literal["asc", "desc"] = "desc",
    ) -> JobSpecification:
        """
        Filters jobs by the given experiment numbers and applies ordering, limit, and offset to the query
        :param experiment_numbers: The experiment numbers linked to the jobs
        :param limit: The maximum number of jobs to return. None indicates no limit.
        :param offset: The number of jobs to skip before starting to return the results. None for no offset.
        :param order_by: The attribute to order the jobs by. Can be attributes of Job or Run entities.
        :param order_direction: The direction to order the jobs, either 'asc' for ascending or 'desc' for
        descending.
        :return: An instance of JobSpecification with the applied filters and ordering.
        """
        self.value = self.value.join(JobOwner).join(Run).where(JobOwner.experiment_number.in_(experiment_numbers))

        self._apply_ordering(order_by, order_direction)

        return self

    @paginate
    def by_instrument(
        self,
        instrument: str,
        limit: int | None = None,
        offset: int | None = None,
        order_by: JointRunJobOrderField = "id",
        order_direction: Literal["asc", "desc"] = "desc",
        user_number: int | None = None,
    ) -> JobSpecification:
        """
        Filters jobs by the specified instrument and applies ordering, limit, and offset to the query.

        :param instrument: The name of the instrument to filter jobs by.
        :param limit: The maximum number of jobs to return. None indicates no limit.
        :param offset: The number of jobs to skip before starting to return the results. None for no offset.
        :param order_by: The attribute to order the jobs by. Can be attributes of Job or Run entities.
        :param order_direction: The direction to order the jobs, either 'asc' for ascending or 'desc' for
        descending.
        :param user_number: The user number by which we should find the experiment numbers.
        :return: An instance of JobSpecification with the applied filters and ordering.
        """
        if user_number:
            experiment_numbers = get_experiments_for_user_number(user_number)
            self.value = (
                self.value.join(JobOwner)
                .join(Instrument)
                .join(Run, Job.run)
                .where(
                    and_(
                        Instrument.instrument_name == instrument,
                        or_(JobOwner.user_number == user_number, JobOwner.experiment_number.in_(experiment_numbers)),
                    )
                )
            )
        else:
            self.value = (self.value.join(Instrument)
                          .where(Instrument.instrument_name == instrument).join(Run, Job.run))

        self._apply_ordering(order_by, order_direction)

        return self

"""
Module defining specifications for querying Reduction entities within the FIA API.

It includes the ReductionSpecification class, which facilitates the construction of complex queries
for fetching Reduction entities based on various criteria such as instrument name, experiment number,
and ordering preferences.
"""

# The limit and offsets in specifications will incorrectly flag as unused. They are used when they are intercepted by
# the paginate decorator
from __future__ import annotations

from typing import Literal

from fia_api.core.auth.experiments import get_experiments_for_user_number
from fia_api.core.model import Instrument, Reduction, Run, run_reduction_junction_table
from fia_api.core.specifications.base import Specification, apply_ordering, paginate

ReductionOrderField = Literal["reduction_start", "reduction_end", "reduction_state", "id", "reduction_outputs"]
RunOrderField = Literal["run_start", "run_end", "experiment_number", "experiment_title", "filename"]
JointRunReductionOrderField = RunOrderField | ReductionOrderField


class ReductionSpecification(Specification[Reduction]):
    """
    A specification class for constructing queries to fetch Reduction entities.

    This class supports filtering and ordering of reductions based on attributes of both
    the Reduction and Run entities, including support for joint attributes.
    """

    @property
    def model(self) -> type[Reduction]:
        return Reduction

    def _apply_ordering(self, order_by: JointRunReductionOrderField, order_direction: Literal["asc", "desc"]) -> None:
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
                self.value = (
                    self.value.order_by(Run.experiment_number.desc())
                    if order_direction == "desc"
                    else self.value.order_by(Run.experiment_number.asc())
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
        order_by: JointRunReductionOrderField = "id",
        order_direction: Literal["asc", "desc"] = "desc",
    ) -> ReductionSpecification:
        """
        Filters reductions by the given experiment numbers and applies ordering, limit, and offset to the query
        :param experiment_numbers: The experiment numbers linked to the reductions
        :param limit: The maximum number of reductions to return. None indicates no limit.
        :param offset: The number of reductions to skip before starting to return the results. None for no offset.
        :param order_by: The attribute to order the reductions by. Can be attributes of Reduction or Run entities.
        :param order_direction: The direction to order the reductions, either 'asc' for ascending or 'desc' for
        descending.
        :return: An instance of ReductionSpecification with the applied filters and ordering.
        """
        self.value = (
            self.value.join(run_reduction_junction_table).join(Run).where(Run.experiment_number.in_(experiment_numbers))
        )

        self._apply_ordering(order_by, order_direction)

        return self

    @paginate
    def by_instrument(
        self,
        instrument: str,
        limit: int | None = None,
        offset: int | None = None,
        order_by: JointRunReductionOrderField = "id",
        order_direction: Literal["asc", "desc"] = "desc",
        user_number: int | None = None,
    ) -> ReductionSpecification:
        """
        Filters reductions by the specified instrument and applies ordering, limit, and offset to the query.

        :param instrument: The name of the instrument to filter reductions by.
        :param limit: The maximum number of reductions to return. None indicates no limit.
        :param offset: The number of reductions to skip before starting to return the results. None for no offset.
        :param order_by: The attribute to order the reductions by. Can be attributes of Reduction or Run entities.
        :param order_direction: The direction to order the reductions, either 'asc' for ascending or 'desc' for
        descending.
        :return: An instance of ReductionSpecification with the applied filters and ordering.
        """
        self.value = (
            self.value.join(run_reduction_junction_table)
            .join(Run)
            .join(Instrument)
            .where(Instrument.instrument_name == instrument)
        )
        if user_number:
            experiment_numbers = get_experiments_for_user_number(user_number)
            self.value = self.value.where(Run.experiment_number.in_(experiment_numbers))

        self._apply_ordering(order_by, order_direction)

        return self

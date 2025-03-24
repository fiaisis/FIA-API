"""Job Owner Specification"""

from __future__ import annotations

from db.data_models import JobOwner
from sqlalchemy import select

from fia_api.core.specifications.base import Specification


class JobOwnerSpecification(Specification[JobOwner]):
    """Job Owner Specification class"""

    @property
    def model(self) -> type[JobOwner]:
        return JobOwner

    def by_values(self, experiment_number: int | None, user_number: int | None) -> JobOwnerSpecification:
        self.value = (
            select(JobOwner)
            .where(JobOwner.experiment_number == experiment_number)
            .where(JobOwner.user_number == user_number)
        )
        return self

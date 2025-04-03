"""Script specification"""

from __future__ import annotations

from db.data_models import Script

from fia_api.core.specifications.base import Specification


class ScriptSpecification(Specification[Script]):
    """Script specification class"""

    @property
    def model(self) -> type[Script]:
        return Script

    def by_script_hash(self, script_hash: str) -> ScriptSpecification:
        """
        Filter scripts by the given hash
        :param script_hash: The hash to filter by
        :return: The query specification
        """
        self.value = self.value.where(Script.script_hash == script_hash)
        return self

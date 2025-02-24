"""PreScript contains the PreScript definition. As it is not strictly a model, it does not belong in models.py"""

from fia_api.core.responses import PreScriptResponse


class PreScript:
    """
    The PreScript is the script obtained from GitHub, prior to being used by the JobController, or being saved to the
    database.
    """

    def __init__(self, value: str, is_latest: bool = False, sha: str | None = None):
        self.value = value
        self._original_value = value
        self.is_latest = is_latest
        self.sha: str | None = sha

    @property
    def original_value(self) -> str:
        """
        Read only original_value is the value before any transforms are applied.
        :return: str - original value  pre transforms
        """
        return self._original_value

    def to_response(self) -> PreScriptResponse:
        """
        Return a ScriptResponse model to be returned by the api
        :return: ScriptResponse - the ScriptResponse
        """
        return PreScriptResponse(value=self.value, is_latest=self.is_latest, sha=self.sha)

    def __repr__(self) -> str:
        return f"PreScript(value={self.value}, is_latest={self.is_latest})"

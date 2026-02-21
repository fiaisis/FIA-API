from enum import Enum


class State(str, Enum):
    ERROR = "ERROR"
    NOT_STARTED = "NOT_STARTED"
    SUCCESSFUL = "SUCCESSFUL"
    UNSUCCESSFUL = "UNSUCCESSFUL"

    def __str__(self) -> str:
        return str(self.value)

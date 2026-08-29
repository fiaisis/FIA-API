from enum import Enum


class GetJobsByInstrumentInstrumentInstrumentJobsGetOrderBy(str, Enum):
    END = "end"
    EXPERIMENT_NUMBER = "experiment_number"
    EXPERIMENT_TITLE = "experiment_title"
    FILENAME = "filename"
    ID = "id"
    OUTPUTS = "outputs"
    RUN_END = "run_end"
    RUN_START = "run_start"
    START = "start"
    STATE = "state"

    def __str__(self) -> str:
        return str(self.value)

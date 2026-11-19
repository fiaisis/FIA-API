import datetime
from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, Union, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field
from dateutil.parser import isoparse

from ..models.state import State

if TYPE_CHECKING:
    from ..models.script_response import ScriptResponse


T = TypeVar("T", bound="JobResponse")


@_attrs_define
class JobResponse:
    """JobResponse object that does not contain the related runs

    Attributes:
        id (int):
        start (Union[None, datetime.datetime]):
        end (Union[None, datetime.datetime]):
        state (State): An enumeration representing the possible reduction states.
        status_message (Union[None, str]):
        inputs (Any):
        outputs (Union[None, str]):
        stacktrace (Union[None, str]):
        script (Union['ScriptResponse', None]):
        runner_image (Union[None, str]):
        type_ (Union[None, str]):
    """

    id: int
    start: Union[None, datetime.datetime]
    end: Union[None, datetime.datetime]
    state: State
    status_message: Union[None, str]
    inputs: Any
    outputs: Union[None, str]
    stacktrace: Union[None, str]
    script: Union["ScriptResponse", None]
    runner_image: Union[None, str]
    type_: Union[None, str]
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        from ..models.script_response import ScriptResponse

        id = self.id

        start: Union[None, str]
        if isinstance(self.start, datetime.datetime):
            start = self.start.isoformat()
        else:
            start = self.start

        end: Union[None, str]
        if isinstance(self.end, datetime.datetime):
            end = self.end.isoformat()
        else:
            end = self.end

        state = self.state.value

        status_message: Union[None, str]
        status_message = self.status_message

        inputs = self.inputs

        outputs: Union[None, str]
        outputs = self.outputs

        stacktrace: Union[None, str]
        stacktrace = self.stacktrace

        script: Union[None, dict[str, Any]]
        if isinstance(self.script, ScriptResponse):
            script = self.script.to_dict()
        else:
            script = self.script

        runner_image: Union[None, str]
        runner_image = self.runner_image

        type_: Union[None, str]
        type_ = self.type_

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "id": id,
                "start": start,
                "end": end,
                "state": state,
                "status_message": status_message,
                "inputs": inputs,
                "outputs": outputs,
                "stacktrace": stacktrace,
                "script": script,
                "runner_image": runner_image,
                "type": type_,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.script_response import ScriptResponse

        d = dict(src_dict)
        id = d.pop("id")

        def _parse_start(data: object) -> Union[None, datetime.datetime]:
            if data is None:
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                start_type_0 = isoparse(data)

                return start_type_0
            except:  # noqa: E722
                pass
            return cast(Union[None, datetime.datetime], data)

        start = _parse_start(d.pop("start"))

        def _parse_end(data: object) -> Union[None, datetime.datetime]:
            if data is None:
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                end_type_0 = isoparse(data)

                return end_type_0
            except:  # noqa: E722
                pass
            return cast(Union[None, datetime.datetime], data)

        end = _parse_end(d.pop("end"))

        state = State(d.pop("state"))

        def _parse_status_message(data: object) -> Union[None, str]:
            if data is None:
                return data
            return cast(Union[None, str], data)

        status_message = _parse_status_message(d.pop("status_message"))

        inputs = d.pop("inputs")

        def _parse_outputs(data: object) -> Union[None, str]:
            if data is None:
                return data
            return cast(Union[None, str], data)

        outputs = _parse_outputs(d.pop("outputs"))

        def _parse_stacktrace(data: object) -> Union[None, str]:
            if data is None:
                return data
            return cast(Union[None, str], data)

        stacktrace = _parse_stacktrace(d.pop("stacktrace"))

        def _parse_script(data: object) -> Union["ScriptResponse", None]:
            if data is None:
                return data
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                script_type_0 = ScriptResponse.from_dict(data)

                return script_type_0
            except:  # noqa: E722
                pass
            return cast(Union["ScriptResponse", None], data)

        script = _parse_script(d.pop("script"))

        def _parse_runner_image(data: object) -> Union[None, str]:
            if data is None:
                return data
            return cast(Union[None, str], data)

        runner_image = _parse_runner_image(d.pop("runner_image"))

        def _parse_type_(data: object) -> Union[None, str]:
            if data is None:
                return data
            return cast(Union[None, str], data)

        type_ = _parse_type_(d.pop("type"))

        job_response = cls(
            id=id,
            start=start,
            end=end,
            state=state,
            status_message=status_message,
            inputs=inputs,
            outputs=outputs,
            stacktrace=stacktrace,
            script=script,
            runner_image=runner_image,
            type_=type_,
        )

        job_response.additional_properties = d
        return job_response

    @property
    def additional_keys(self) -> list[str]:
        return list(self.additional_properties.keys())

    def __getitem__(self, key: str) -> Any:
        return self.additional_properties[key]

    def __setitem__(self, key: str, value: Any) -> None:
        self.additional_properties[key] = value

    def __delitem__(self, key: str) -> None:
        del self.additional_properties[key]

    def __contains__(self, key: str) -> bool:
        return key in self.additional_properties

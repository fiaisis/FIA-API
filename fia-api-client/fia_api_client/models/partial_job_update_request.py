from collections.abc import Mapping
from typing import Any, TypeVar, Union, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.state import State
from ..types import UNSET, Unset

T = TypeVar("T", bound="PartialJobUpdateRequest")


@_attrs_define
class PartialJobUpdateRequest:
    """Partial Job Update Request encompasses all the safely updatable fields on a Job

    Attributes:
        state (Union[None, State, Unset]):
        status_message (Union[None, Unset, str]):
        outputs (Union[None, Unset, str]):
        start (Union[None, Unset, str]):
        stacktrace (Union[None, Unset, str]):
        end (Union[None, Unset, str]):
    """

    state: Union[None, State, Unset] = UNSET
    status_message: Union[None, Unset, str] = UNSET
    outputs: Union[None, Unset, str] = UNSET
    start: Union[None, Unset, str] = UNSET
    stacktrace: Union[None, Unset, str] = UNSET
    end: Union[None, Unset, str] = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        state: Union[None, Unset, str]
        if isinstance(self.state, Unset):
            state = UNSET
        elif isinstance(self.state, State):
            state = self.state.value
        else:
            state = self.state

        status_message: Union[None, Unset, str]
        if isinstance(self.status_message, Unset):
            status_message = UNSET
        else:
            status_message = self.status_message

        outputs: Union[None, Unset, str]
        if isinstance(self.outputs, Unset):
            outputs = UNSET
        else:
            outputs = self.outputs

        start: Union[None, Unset, str]
        if isinstance(self.start, Unset):
            start = UNSET
        else:
            start = self.start

        stacktrace: Union[None, Unset, str]
        if isinstance(self.stacktrace, Unset):
            stacktrace = UNSET
        else:
            stacktrace = self.stacktrace

        end: Union[None, Unset, str]
        if isinstance(self.end, Unset):
            end = UNSET
        else:
            end = self.end

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if state is not UNSET:
            field_dict["state"] = state
        if status_message is not UNSET:
            field_dict["status_message"] = status_message
        if outputs is not UNSET:
            field_dict["outputs"] = outputs
        if start is not UNSET:
            field_dict["start"] = start
        if stacktrace is not UNSET:
            field_dict["stacktrace"] = stacktrace
        if end is not UNSET:
            field_dict["end"] = end

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)

        def _parse_state(data: object) -> Union[None, State, Unset]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                state_type_0 = State(data)

                return state_type_0
            except:  # noqa: E722
                pass
            return cast(Union[None, State, Unset], data)

        state = _parse_state(d.pop("state", UNSET))

        def _parse_status_message(data: object) -> Union[None, Unset, str]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, str], data)

        status_message = _parse_status_message(d.pop("status_message", UNSET))

        def _parse_outputs(data: object) -> Union[None, Unset, str]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, str], data)

        outputs = _parse_outputs(d.pop("outputs", UNSET))

        def _parse_start(data: object) -> Union[None, Unset, str]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, str], data)

        start = _parse_start(d.pop("start", UNSET))

        def _parse_stacktrace(data: object) -> Union[None, Unset, str]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, str], data)

        stacktrace = _parse_stacktrace(d.pop("stacktrace", UNSET))

        def _parse_end(data: object) -> Union[None, Unset, str]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, str], data)

        end = _parse_end(d.pop("end", UNSET))

        partial_job_update_request = cls(
            state=state,
            status_message=status_message,
            outputs=outputs,
            start=start,
            stacktrace=stacktrace,
            end=end,
        )

        partial_job_update_request.additional_properties = d
        return partial_job_update_request

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

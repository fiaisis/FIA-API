import datetime
from collections.abc import Mapping
from typing import Any, TypeVar, Union, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field
from dateutil.parser import isoparse

T = TypeVar("T", bound="RunResponse")


@_attrs_define
class RunResponse:
    """Run Response object

    Attributes:
        filename (str):
        experiment_number (Union[None, int]):
        title (str):
        users (str):
        run_start (datetime.datetime):
        run_end (datetime.datetime):
        good_frames (int):
        raw_frames (int):
        instrument_name (str):
    """

    filename: str
    experiment_number: Union[None, int]
    title: str
    users: str
    run_start: datetime.datetime
    run_end: datetime.datetime
    good_frames: int
    raw_frames: int
    instrument_name: str
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        filename = self.filename

        experiment_number: Union[None, int]
        experiment_number = self.experiment_number

        title = self.title

        users = self.users

        run_start = self.run_start.isoformat()

        run_end = self.run_end.isoformat()

        good_frames = self.good_frames

        raw_frames = self.raw_frames

        instrument_name = self.instrument_name

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "filename": filename,
                "experiment_number": experiment_number,
                "title": title,
                "users": users,
                "run_start": run_start,
                "run_end": run_end,
                "good_frames": good_frames,
                "raw_frames": raw_frames,
                "instrument_name": instrument_name,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        filename = d.pop("filename")

        def _parse_experiment_number(data: object) -> Union[None, int]:
            if data is None:
                return data
            return cast(Union[None, int], data)

        experiment_number = _parse_experiment_number(d.pop("experiment_number"))

        title = d.pop("title")

        users = d.pop("users")

        run_start = isoparse(d.pop("run_start"))

        run_end = isoparse(d.pop("run_end"))

        good_frames = d.pop("good_frames")

        raw_frames = d.pop("raw_frames")

        instrument_name = d.pop("instrument_name")

        run_response = cls(
            filename=filename,
            experiment_number=experiment_number,
            title=title,
            users=users,
            run_start=run_start,
            run_end=run_end,
            good_frames=good_frames,
            raw_frames=raw_frames,
            instrument_name=instrument_name,
        )

        run_response.additional_properties = d
        return run_response

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

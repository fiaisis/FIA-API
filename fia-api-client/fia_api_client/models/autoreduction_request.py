from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

if TYPE_CHECKING:
    from ..models.autoreduction_request_additional_values import AutoreductionRequestAdditionalValues


T = TypeVar("T", bound="AutoreductionRequest")


@_attrs_define
class AutoreductionRequest:
    """Autoreduction request encompasses all the fields necessary for an autoreduction job to be created

    Attributes:
        filename (str):
        rb_number (str):
        instrument_name (str):
        title (str):
        users (str):
        run_start (str):
        run_end (str):
        good_frames (int):
        raw_frames (int):
        additional_values (AutoreductionRequestAdditionalValues):
        runner_image (str):
    """

    filename: str
    rb_number: str
    instrument_name: str
    title: str
    users: str
    run_start: str
    run_end: str
    good_frames: int
    raw_frames: int
    additional_values: "AutoreductionRequestAdditionalValues"
    runner_image: str
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        filename = self.filename

        rb_number = self.rb_number

        instrument_name = self.instrument_name

        title = self.title

        users = self.users

        run_start = self.run_start

        run_end = self.run_end

        good_frames = self.good_frames

        raw_frames = self.raw_frames

        additional_values = self.additional_values.to_dict()

        runner_image = self.runner_image

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "filename": filename,
                "rb_number": rb_number,
                "instrument_name": instrument_name,
                "title": title,
                "users": users,
                "run_start": run_start,
                "run_end": run_end,
                "good_frames": good_frames,
                "raw_frames": raw_frames,
                "additional_values": additional_values,
                "runner_image": runner_image,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.autoreduction_request_additional_values import AutoreductionRequestAdditionalValues

        d = dict(src_dict)
        filename = d.pop("filename")

        rb_number = d.pop("rb_number")

        instrument_name = d.pop("instrument_name")

        title = d.pop("title")

        users = d.pop("users")

        run_start = d.pop("run_start")

        run_end = d.pop("run_end")

        good_frames = d.pop("good_frames")

        raw_frames = d.pop("raw_frames")

        additional_values = AutoreductionRequestAdditionalValues.from_dict(d.pop("additional_values"))

        runner_image = d.pop("runner_image")

        autoreduction_request = cls(
            filename=filename,
            rb_number=rb_number,
            instrument_name=instrument_name,
            title=title,
            users=users,
            run_start=run_start,
            run_end=run_end,
            good_frames=good_frames,
            raw_frames=raw_frames,
            additional_values=additional_values,
            runner_image=runner_image,
        )

        autoreduction_request.additional_properties = d
        return autoreduction_request

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

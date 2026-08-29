from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

T = TypeVar("T", bound="RerunJob")


@_attrs_define
class RerunJob:
    """
    Attributes:
        job_id (int):
        runner_image (str):
        script (str):
    """

    job_id: int
    runner_image: str
    script: str
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        job_id = self.job_id

        runner_image = self.runner_image

        script = self.script

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "job_id": job_id,
                "runner_image": runner_image,
                "script": script,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        job_id = d.pop("job_id")

        runner_image = d.pop("runner_image")

        script = d.pop("script")

        rerun_job = cls(
            job_id=job_id,
            runner_image=runner_image,
            script=script,
        )

        rerun_job.additional_properties = d
        return rerun_job

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

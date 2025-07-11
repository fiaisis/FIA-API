"""SQLAlchemy Models and related classes"""

from __future__ import annotations

import enum
from datetime import datetime
from typing import Literal

from sqlalchemy import Enum, ForeignKey, Integer, inspect
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.engine.default import DefaultExecutionContext
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

from fia_api.core.utility import hash_script


class State(enum.Enum):
    """
    An enumeration representing the possible reduction states.
    """

    SUCCESSFUL = "SUCCESSFUL"
    UNSUCCESSFUL = "UNSUCCESSFUL"
    ERROR = "ERROR"
    NOT_STARTED = "NOT_STARTED"


class JobType(enum.Enum):
    """
    An enumeration representing the possible reduction states.
    """

    RERUN = "RERUN"
    SIMPLE = "SIMPLE"
    AUTOREDUCTION = "AUTOREDUCTION"


class Base(DeclarativeBase):
    """
    Base class for SQLAlchemy ORM models. It includes a primary key `id` attribute, and defines equality as deep
    equality.
    """

    id: Mapped[int] = mapped_column(primary_key=True)

    def __hash__(self) -> int:
        return hash(self.id)

    def __eq__(self, other: object) -> bool:
        """
        Check if two instances of Base are equal by comparing the values of their column attributes.

        :param other: The other instance of Base to compare with.
        :return: True if the instances are equal, False otherwise.
        """
        if not isinstance(other, Base):
            return False
        # Ignores due to inspect returning Any, includes None, by default
        return {attr.key: getattr(self, attr.key) for attr in inspect(self).mapper.column_attrs} == {
            attr.key: getattr(other, attr.key) for attr in inspect(other).mapper.column_attrs
        }


def create_default_hash(context: DefaultExecutionContext) -> str:
    """
    Generate a hash for the `script` field of the current parameters in the database context.

    This function extracts the `script` field from the current parameters and applies the `hash_script` utility
    to compute its hash. The resulting hash value is used as the default or updated value for the `script_hash` field.

    :param context: The SQLAlchemy execution context dictionary containing the current parameters.
    :return: A hash string derived from the `script` field.
    """
    return hash_script(context.get_current_parameters()["script"])  # type: ignore


class Script(Base):
    """
    The Script class represents a script in the database.
    """

    __tablename__ = "scripts"
    script: Mapped[str] = mapped_column()
    sha: Mapped[str | None] = mapped_column()
    script_hash: Mapped[str] = mapped_column(default=create_default_hash, onupdate=create_default_hash)

    def __repr__(self) -> str:
        return f"Script(id={self.id}, sha='{self.sha}', script_hash='{self.script_hash}', value='{self.script}')"


class JobOwner(Base):
    __tablename__ = "job_owners"
    experiment_number: Mapped[int | None] = mapped_column(unique=True)
    user_number: Mapped[int | None] = mapped_column(unique=True)


class Job(Base):
    """
    The Job class represents a reduction in the database.
    """

    __tablename__ = "jobs"
    start: Mapped[datetime | None] = mapped_column()
    end: Mapped[datetime | None] = mapped_column()
    state: Mapped[State] = mapped_column(Enum(State))
    status_message: Mapped[str | None] = mapped_column()
    inputs: Mapped[JSONB] = mapped_column(JSONB)
    script_id: Mapped[int | None] = mapped_column(ForeignKey("scripts.id"))
    script: Mapped[Script | None] = relationship("Script", lazy="joined")
    outputs: Mapped[str | None] = mapped_column()
    stacktrace: Mapped[str | None] = mapped_column()
    runner_image: Mapped[str | None] = mapped_column()
    owner_id: Mapped[int] = mapped_column(ForeignKey("job_owners.id"))
    owner: Mapped[JobOwner | None] = relationship("JobOwner", lazy="joined")
    instrument_id: Mapped[int | None] = mapped_column(ForeignKey("instruments.id"))
    instrument: Mapped[Instrument | None] = relationship("Instrument", lazy="joined")
    job_type: Mapped[JobType] = mapped_column(Enum(JobType))
    run_id: Mapped[int | None] = mapped_column(ForeignKey("runs.id"))
    run: Mapped[Run | None] = relationship(back_populates="jobs", lazy="joined")

    def __repr__(self) -> str:
        return (
            f"Job(id={self.id}, start={self.start}, end={self.end}, state={self.state}, inputs={self.inputs}, "
            f"outputs={self.outputs}, script_id={self.script_id})"
        )


class Instrument(Base):
    """
    The Instrument Table's declarative declaration
    """

    __tablename__ = "instruments"
    instrument_name: Mapped[str] = mapped_column(unique=True)
    latest_run: Mapped[str | None] = mapped_column()
    specification: Mapped[JSONB | None] = mapped_column(JSONB)

    def __hash__(self) -> int:
        return hash(self.instrument_name)

    def __eq__(self, other: object) -> bool:
        if isinstance(other, Instrument):
            return bool(self.instrument_name == other.instrument_name and self.latest_run == other.latest_run)
        return False

    def __repr__(self) -> str:
        return f"<Instrument(id={self.id}, instrument_name={self.instrument_name}, latest_run={self.latest_run})>"


class Run(Base):
    """
    The Run table's declarative declaration
    """

    __tablename__ = "runs"
    filename: Mapped[str] = mapped_column()
    instrument_id: Mapped[int] = mapped_column(ForeignKey("instruments.id"))
    instrument: Mapped[Instrument] = relationship("Instrument", lazy="joined")
    title: Mapped[str] = mapped_column()
    users: Mapped[str] = mapped_column()
    run_start: Mapped[datetime] = mapped_column()
    run_end: Mapped[datetime] = mapped_column()
    good_frames: Mapped[int] = mapped_column(Integer())
    raw_frames: Mapped[int] = mapped_column(Integer())
    owner_id: Mapped[int] = mapped_column(ForeignKey("job_owners.id"))
    owner: Mapped[JobOwner | None] = relationship("JobOwner", lazy="joined")
    jobs: Mapped[list[Job] | None] = relationship(back_populates="run", lazy="joined")

    def __hash__(self) -> int:
        return hash(f"{self.title}{self.id}")

    def __eq__(self, other: object) -> bool:
        if isinstance(other, Run):
            return (
                self.filename == other.filename
                and self.title == other.title
                and self.instrument_id == other.instrument_id
                and self.users == other.users
                and self.owner_id == other.owner_id
                and self.run_start == other.run_start
                and self.run_end == other.run_end
                and self.good_frames == other.good_frames
                and self.raw_frames == other.raw_frames
            )
        return False

    def __repr__(self) -> str:
        return (
            f"<Run(id={self.id}, filename={self.filename}, instrument_id={self.instrument_id}, title={self.title},"
            f" users={self.users}, owner_id={self.owner_id}, run_start={self.run_start},"
            f" run_end={self.run_end}, good_frames={self.good_frames}, raw_frames={self.raw_frames})>"
        )


InstrumentString = Literal[
    "alf",
    "argus",
    "chipir",
    "chronus",
    "crisp",
    "emu",
    "enginx",
    "gem",
    "hifi",
    "hrpd",
    "imat",
    "ines",
    "inter",
    "iris",
    "larmor",
    "let",
    "loq",
    "maps",
    "mari",
    "merlin",
    "musr",
    "nimrod",
    "offspec",
    "osiris",
    "pearl",
    "polaris",
    "polref",
    "sandals",
    "sans2d",
    "surf",
    "sxd",
    "tosca",
    "vesuvio",
    "wish",
    "zoom",
    "test",
    "test",
]

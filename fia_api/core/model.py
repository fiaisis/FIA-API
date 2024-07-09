"""
This module contains classes and enums that define the structure of the database tables and relationships for storing
information about instruments, runs, scripts, and reductions.
"""

from __future__ import annotations

import enum
from datetime import datetime  # need to keep this for sqlalchemy inference

from sqlalchemy import (
    Column,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    String,
    Table,
    inspect,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class ReductionState(enum.Enum):
    """
    An enumeration representing the possible reduction states.
    """

    SUCCESSFUL = "SUCCESSFUL"
    UNSUCCESSFUL = "UNSUCCESSFUL"
    ERROR = "ERROR"
    NOT_STARTED = "NOT_STARTED"


class Base(DeclarativeBase):
    """
    Base class for SQLAlchemy ORM models. It includes a primary key `id` attribute, and defines equality as deep
    equality.
    """

    id: Mapped[int] = mapped_column(primary_key=True)

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


run_reduction_junction_table = Table(
    "runs_reductions",
    Base.metadata,
    Column("run_id", ForeignKey("runs.id")),
    Column("reduction_id", ForeignKey("reductions.id")),
)


class Script(Base):
    """
    The Script class represents a script in the database.
    """

    __tablename__ = "scripts"
    script: Mapped[str] = mapped_column(String())
    sha: Mapped[str | None] = mapped_column(String())
    script_hash: Mapped[str] = mapped_column(String())

    def __repr__(self) -> str:
        return f"Script(id={self.id}, sha='{self.sha}', script_hash='{self.script_hash}', value='{self.script}')"


class Reduction(Base):
    """
    The Reduction class represents a reduction in the database.
    """

    __tablename__ = "reductions"
    reduction_start: Mapped[datetime | None] = mapped_column(DateTime())
    reduction_end: Mapped[datetime | None] = mapped_column(DateTime())
    reduction_state: Mapped[ReductionState] = mapped_column(Enum(ReductionState))
    reduction_status_message: Mapped[str | None] = mapped_column(String())
    reduction_inputs: Mapped[JSONB] = mapped_column(JSONB)
    reduction_outputs: Mapped[str | None] = mapped_column(String())
    stacktrace: Mapped[str | None] = mapped_column(String())
    script_id: Mapped[int | None] = mapped_column(ForeignKey("scripts.id"))
    script: Mapped[Script | None] = relationship("Script", lazy="joined")
    runs: Mapped[list[Run]] = relationship(
        secondary=run_reduction_junction_table,
        back_populates="reductions",
        lazy="subquery",
    )

    def __repr__(self) -> str:
        return (
            f"Reduction(id={self.id}, reduction_start={self.reduction_start}, reduction_end={self.reduction_end}"
            f", reduction_state={self.reduction_state}, reduction_inputs={self.reduction_inputs},"
            f" reduction_outputs={self.reduction_outputs}, script_id={self.script_id})"
        )


class Instrument(Base):
    """
    The Instrument class represents an instrument in the database.
    """

    __tablename__ = "instruments"
    instrument_name: Mapped[str] = mapped_column(String())
    specification: Mapped[JSONB] = mapped_column(JSONB)

    def __repr__(self) -> str:
        return f"Instrument(id={self.id}, instrument_name={self.instrument_name})"


class Run(Base):
    """
    The Run class represents a run in the database.
    """

    __tablename__ = "runs"
    filename: Mapped[str] = mapped_column(String())
    experiment_number: Mapped[int] = mapped_column(Integer())
    title: Mapped[str] = mapped_column(String())
    users: Mapped[str] = mapped_column(String())
    run_start: Mapped[datetime] = mapped_column(DateTime())
    run_end: Mapped[datetime] = mapped_column(DateTime())
    good_frames: Mapped[int] = mapped_column(Integer())
    raw_frames: Mapped[int] = mapped_column(Integer())
    instrument_id: Mapped[int] = mapped_column(ForeignKey("instruments.id"))
    instrument: Mapped[Instrument] = relationship("Instrument", lazy="subquery")
    reductions: Mapped[list[Reduction]] = relationship(
        secondary=run_reduction_junction_table, back_populates="runs", lazy="subquery"
    )

    def __repr__(self) -> str:
        return (
            f"Run(id={self.id}, filename={self.filename}, experiment_number={self.experiment_number}, "
            f"title={self.title}, users={self.users}, run_start={self.run_start}, run_end={self.run_end}, "
            f"good_frames={self.good_frames}, raw_frames={self.raw_frames}, instrument_id={self.instrument_id})"
        )

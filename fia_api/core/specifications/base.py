"""
Base Specification Module

Defines the abstract base class for creating query specifications.
These specifications are designed to encapsulate the logic for querying the database,
allowing for reusable and composable query objects. This approach aims to separate
the concerns of how objects are retrieved from the database from the rest of the application logic.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Callable
from functools import wraps
from typing import Any, Generic, Literal, TypeVar

from db.data_models import Base
from sqlalchemy import Select, select

T = TypeVar("T", bound=Base)


def apply_pagination(spec_value: Select[tuple[T]], limit: int, offset: int) -> Select[tuple[T]]:
    """
    Given a Select of T, apply given limits and offsets
    :param spec_value: The Select
    :param limit: The limit
    :param offset: The offset
    :return: The select with limits and offsets applied
    """
    if limit:
        spec_value = spec_value.limit(limit)
    if offset:
        spec_value = spec_value.offset(offset)
    return spec_value


def apply_ordering(
    spec_value: Select[tuple[T]],
    model: type[T],
    order_by: str,
    order_direction: str,
) -> Select[tuple[T]]:
    """
    Apply basic ordering to the specification value.
    Note: This can only be called when there are no joins. Orders based on relations should be implemented in the
    specification method directly
    :param spec_value:
    :param model:
    :param order_by:
    :param order_direction:
    :return:
    """
    column_element = getattr(model, order_by)
    return (
        spec_value.order_by(column_element.asc())
        if order_direction == "asc"
        else spec_value.order_by(column_element.desc())
    )


def paginate(func: Callable[..., Any]) -> Callable[..., Any]:
    """
    This decorator allows any specification method to accept the args limit: int and offset: int
    and will apply them to the specifications query automagically. This means that the limit and offset args
    will appear to be unused in the specification method, but they are not.
    :param func:  The specification Method
    :return: Wrapped specification method with pagination
    """

    @wraps(func)
    def wrapper(self: Specification[T], *args: tuple[Any], **kwargs: int) -> Any:
        limit = kwargs.get("limit", 0)
        offset = kwargs.get("offset", 0)
        self.value = apply_pagination(self.value, limit, offset)
        return func(self, *args, **kwargs)

    return wrapper


class Specification(Generic[T], ABC):
    """
    An abstract base class that defines a generic query specification for an ORM model.

    This class is designed to be subclassed by specific query specification implementations
    that define how to retrieve instances of ORM models based on various criteria.
    """

    def __init__(self) -> None:
        self.value: Select[tuple[T]] = select(self.model)

    @property
    @abstractmethod
    def model(self) -> type[T]:
        """
        An abstract property that should be overridden to return the SQLAlchemy model class
        that the specification is targeting.

        This property enables the specification to construct queries dynamically based on the model class.

        :return: The SQLAlchemy model class that this specification targets.
        """

    def all(
        self,
        limit: int = 0,
        offset: int = 0,
        order_by: str = "id",
        order_direction: Literal["asc", "desc"] = "desc",
    ) -> Specification[T]:
        """
        Initializes the specification with a query that selects all records of the model.

        This method can be used to start a query specification that retrieves all instances
        of the specified model from the database.

        :return: An instance of the specification class with the query initialized to select all records.
        """
        self.value = select(self.model)
        # We can't decorate this method like inherited ones, as there is not a clean way to inherit the decorator
        # metaclass hacks
        self.value = apply_pagination(self.value, limit, offset)
        self.value = apply_ordering(self.value, self.model, order_by, order_direction)

        return self

    def by_id(self, id_: int) -> Specification[T]:
        """
        Filters the query to select only the record with the specified primary key ID.

        This method is a common specification that can be used to retrieve a single instance
        of the model based on its primary key.

        :param id_: The primary key ID of the model instance to retrieve.
        :return: An instance of the specification class with the query filtered by the specified ID.
        """
        self.value = select(self.model).where(self.model.id == id_)
        return self

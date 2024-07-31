"""
Provides a generic repository class for performing database operations.
"""

import logging
import os
from collections.abc import Sequence
from typing import Generic, TypeVar

from sqlalchemy import NullPool, create_engine, func, select
from sqlalchemy.exc import MultipleResultsFound, NoResultFound
from sqlalchemy.orm import sessionmaker

from fia_api.core.exceptions import NonUniqueRecordError
from fia_api.core.model import Base
from fia_api.core.specifications.base import Specification

T = TypeVar("T", bound=Base)

logger = logging.getLogger(__name__)

DB_USERNAME = os.environ.get("DB_USERNAME", "postgres")
DB_PASSWORD = os.environ.get("DB_PASSWORD", "password")
DB_IP = os.environ.get("DB_IP", "localhost")

ENGINE = create_engine(
    f"postgresql+psycopg2://{DB_USERNAME}:{DB_PASSWORD}@{DB_IP}:5432/fia",
    poolclass=NullPool,
)

SESSION = sessionmaker(ENGINE)


def test_connection():
    """Test connection to database."""
    with SESSION() as session:
        session.execute(select(1))


class Repo(Generic[T]):
    """
    A generic repository class for performing database operations on entities of type T.

    This class provides methods to find one or multiple entities based on a specification,
    and to count entities matching a specification. It is designed to work with any entity
    that inherits from the base model class.
    """

    def __init__(self) -> None:
        self._session = SESSION

    def find(self, spec: Specification[T]) -> Sequence[T]:
        """
        Finds entities matching the given specification.

        :param spec: A specification defining the query criteria.
        :return: A sequence of entities of type T that match the specification.
        """
        with self._session() as session:
            query = spec.value
            return session.execute(query).scalars().all()

    def find_one(self, spec: Specification[T]) -> T | None:
        """
        Finds a single entity matching the given specification.

        If no entities are found, None is returned. If multiple entities are found,
        a NonUniqueRecordError is raised.

        :param spec: A specification defining the query criteria.
        :return: An entity of type T that matches the specification, or None if no entities are found.
        :raises NonUniqueRecordError: If more than one entity matches the specification.
        """
        with self._session() as session:
            try:
                return session.execute(spec.value).scalars().one()
            except NoResultFound:
                logger.exception("No result found for %s", spec.value)
                return None
            except MultipleResultsFound as exc:
                logger.exception("Non unique record found for %s", spec.value)
                raise NonUniqueRecordError() from exc

    def count(self, spec: Specification[T]) -> int:
        """
        Counts the number of entities matching the given specification.

        :param spec: A specification defining the query criteria.
        :return: The count of entities of type T that match the specification.
        """
        with self._session() as session:
            # pylint: disable = not-callable
            # mypy does not like these, but they are valid.
            result = session.execute(select(func.count()).select_from(spec.value))  # type: ignore
            # pylint: enable = not-callable
            return result.scalar() if result else 0  # type: ignore

    def update_one(self, entity: T) -> T:
        """
        Updates the given entity
        :param entity: The entity to be updated
        :return: The updated Entity
        """
        with self._session() as session:
            session.add(entity)
            session.commit()
            session.refresh(entity)
        return entity

"""Script to generate a database for a development environment"""

import os
import random
import sys

from db.data_models import Base
from faker import Faker
from sqlalchemy import NullPool, create_engine
from sqlalchemy.orm import sessionmaker

from test.utils import FIA_FAKER_PROVIDER, FIAProvider

random.seed(1)
Faker.seed(1)
faker = Faker()

DB_USERNAME = os.environ.get("DB_USERNAME", "postgres")
DB_PASSWORD = os.environ.get("DB_PASSWORD", "password")
DB_IP = os.environ.get("DB_IP", "localhost")

ENGINE = create_engine(
    f"postgresql+psycopg2://{DB_USERNAME}:{DB_PASSWORD}@{DB_IP}:5432/fia",
    poolclass=NullPool,
    echo=True,
)

SESSION = sessionmaker(ENGINE)


def main():
    """Start DB Generator"""
    fia_provider = FIA_FAKER_PROVIDER

    if "localhost" not in ENGINE.url:
        # Someone already overwrote all of production with this. Proceed with caution.
        sys.exit(f"Script is not pointing at localhost {ENGINE.url}: Don't even think about it")

    Base.metadata.drop_all(ENGINE)
    Base.metadata.create_all(ENGINE)

    with SESSION() as session:
        instruments = []
        for instrument in FIAProvider.INSTRUMENTS:
            instrument_ = FIAProvider(faker).instrument()
            instrument_.instrument_name = instrument
            instruments.append(instrument_)

        for _ in range(10000):
            session.add(fia_provider.insertable_job(random.choice(instruments)))  # noqa: S311
        session.commit()


if __name__ == "__main__":
    main()

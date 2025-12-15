import os

from sqlalchemy import NullPool, create_engine
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import sessionmaker

DB_USERNAME = os.environ.get("DB_USERNAME", "postgres")
DB_PASSWORD = os.environ.get("DB_PASSWORD", "password")
DB_IP = os.environ.get("DB_IP", "localhost")

ENGINE = create_engine(
    f"postgresql+psycopg2://{DB_USERNAME}:{DB_PASSWORD}@{DB_IP}:5432/fia",
    poolclass=NullPool,
)

SESSION = sessionmaker(ENGINE)


async def create_session() -> AsyncSession:
    db = SESSION()
    try:
        yield db
    finally:
        db.close()

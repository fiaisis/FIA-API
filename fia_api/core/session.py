import os
from typing import Generator

from sqlalchemy import NullPool, create_engine 
from sqlalchemy.orm import sessionmaker, Session

DB_USERNAME = os.environ.get("DB_USERNAME", "postgres")
DB_PASSWORD = os.environ.get("DB_PASSWORD", "password")
DB_IP = os.environ.get("DB_IP", "localhost")
DB_URL = (
    f"postgresql+psycopg2://{DB_USERNAME}:{DB_PASSWORD}@{DB_IP}:5432/fia"
)

ENGINE = create_engine(
    DB_URL,
    poolclass=NullPool,
)

SessionLocal = sessionmaker(
    bind=ENGINE,
    autoflush=False,
    autocommit=False
)


def get_db_session() -> Generator[Session, None, None]:
    db = SessionLocal()
      try:
          yield db
      finally:
          db.close()

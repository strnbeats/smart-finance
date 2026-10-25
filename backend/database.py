from pathlib import Path

from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import DeclarativeBase, sessionmaker


PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATABASE_PATH = PROJECT_ROOT / "data" / "smart_finance.db"

DATABASE_URL = f"sqlite:///{DATABASE_PATH}"

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},
)

SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
)


class Base(DeclarativeBase):
    pass


def init_db():
    from backend import models

    DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)

    Base.metadata.create_all(bind=engine)

    inspector = inspect(engine)
    columns = {
        column["name"]
        for column in inspector.get_columns("transactions")
    }

    if "mcc" not in columns:
        with engine.begin() as connection:
            connection.execute(
                text(
                    "ALTER TABLE transactions "
                    "ADD COLUMN mcc VARCHAR(4)"
                )
            )

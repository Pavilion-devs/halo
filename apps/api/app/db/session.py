from collections.abc import Generator

from sqlalchemy import inspect, text
from sqlmodel import Session, SQLModel, create_engine

from app.core.config import settings

connect_args = {"check_same_thread": False} if settings.database_url.startswith("sqlite") else {}
engine = create_engine(settings.database_url, connect_args=connect_args)


def create_db_and_tables() -> None:
    SQLModel.metadata.create_all(engine)
    _ensure_approval_columns()


def get_session() -> Generator[Session, None, None]:
    with Session(engine) as session:
        yield session


def _ensure_approval_columns() -> None:
    """create_all does not alter existing SQLite tables during local demos."""
    if not settings.database_url.startswith("sqlite"):
        return

    expected_columns = {
        "external_system": "VARCHAR",
        "external_action_id": "VARCHAR",
        "external_status": "VARCHAR",
        "risk": "VARCHAR",
        "title": "VARCHAR",
        "details": "JSON",
    }
    inspector = inspect(engine)
    if "approvals" not in inspector.get_table_names():
        return
    existing_columns = {column["name"] for column in inspector.get_columns("approvals")}
    with engine.begin() as connection:
        for column_name, column_type in expected_columns.items():
            if column_name not in existing_columns:
                connection.execute(
                    text(f"ALTER TABLE approvals ADD COLUMN {column_name} {column_type}")
                )

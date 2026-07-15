from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from app.core.config import get_settings


settings = get_settings()
connect_args = {"check_same_thread": False} if settings.database_url.startswith("sqlite") else {}
engine = create_engine(settings.database_url, connect_args=connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def ensure_schema_compatibility():
    if not settings.database_url.startswith("sqlite"):
        return
    inspector = inspect(engine)
    if "emergency_contacts" not in inspector.get_table_names():
        return
    columns = {column["name"] for column in inspector.get_columns("emergency_contacts")}
    with engine.begin() as connection:
        if "telegram_username" not in columns:
            connection.execute(text("ALTER TABLE emergency_contacts ADD COLUMN telegram_username VARCHAR(120)"))

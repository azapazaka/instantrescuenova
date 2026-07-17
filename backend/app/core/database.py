from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker
from sqlalchemy.pool import NullPool

from app.core.config import get_settings


settings = get_settings()

if settings.database_url.startswith("sqlite"):
    engine = create_engine(settings.database_url, connect_args={"check_same_thread": False})
else:
    # Vercel functions are short-lived but can stay warm. A normal SQLAlchemy
    # pool would keep Postgres sessions open across warm lambdas and can exhaust
    # the Supabase session pooler during normal app navigation.
    engine = create_engine(settings.database_url, pool_pre_ping=True, poolclass=NullPool)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

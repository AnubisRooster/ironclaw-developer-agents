"""PostgreSQL connection management using SQLAlchemy + psycopg2.

Provides engine creation, session factory, and schema initialisation.
All tables are defined in ``database.models`` and created here on first use.
"""

from __future__ import annotations

import logging
from contextlib import contextmanager
from typing import Generator

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from security.secrets import get_secrets

logger = logging.getLogger("claw-agent.database")

_engine: Engine | None = None
_SessionLocal: sessionmaker | None = None


def get_engine() -> Engine:
    """Return the singleton SQLAlchemy engine (creates on first call)."""
    global _engine
    if _engine is None:
        url = get_secrets().database_url
        _engine = create_engine(
            url,
            echo=False,
            pool_size=5,
            max_overflow=10,
            pool_pre_ping=True,
        )
        from database.models import Base
        Base.metadata.create_all(_engine)
        logger.info("PostgreSQL engine created: %s", url.split("@")[-1] if "@" in url else url)
    return _engine


def get_session_factory() -> sessionmaker:
    """Return the singleton session factory."""
    global _SessionLocal
    if _SessionLocal is None:
        _SessionLocal = sessionmaker(bind=get_engine())
    return _SessionLocal


def get_session() -> Session:
    """Open and return a new database session."""
    return get_session_factory()()


@contextmanager
def session_scope() -> Generator[Session, None, None]:
    """Context manager that commits on success and rolls back on error."""
    session = get_session()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def check_connection() -> bool:
    """Verify the PostgreSQL connection is alive."""
    try:
        with get_engine().connect() as conn:
            conn.execute(text("SELECT 1"))
        return True
    except Exception as exc:
        logger.error("Database connection check failed: %s", exc)
        return False

"""
Database connection and session management
"""

from contextlib import asynccontextmanager
from typing import Generator, Optional

from sqlalchemy import create_engine, event
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import QueuePool

from laas.core.config import get_settings


class DatabaseManager:
    """Database connection manager with multi-tenant support"""

    def __init__(self):
        self.settings = get_settings()
        self.engine = self._create_engine()
        self.SessionLocal = sessionmaker(
            autocommit=False, autoflush=False, bind=self.engine
        )

    def _create_engine(self) -> Engine:
        """Create database engine with connection pooling"""
        engine = create_engine(
            self.settings.database_url,
            poolclass=QueuePool,
            pool_size=self.settings.database_pool_size,
            max_overflow=self.settings.database_max_overflow,
            pool_pre_ping=True,
            pool_recycle=3600,  # Recycle connections every hour
            echo=self.settings.debug,
        )

        # Add connection event listeners
        @event.listens_for(engine, "connect")
        def set_sqlite_pragma(dbapi_connection, connection_record):
            """Set database connection parameters"""
            if "postgresql" in self.settings.database_url:
                # PostgreSQL specific settings
                with dbapi_connection.cursor() as cursor:
                    cursor.execute("SET timezone TO 'UTC'")

        return engine

    def get_session(self) -> Generator[Session, None, None]:
        """Get database session"""
        session = self.SessionLocal()
        try:
            yield session
        finally:
            session.close()

    def get_tenant_session(self, tenant_id: str) -> Generator[Session, None, None]:
        """Get tenant-specific database session"""
        session = self.SessionLocal()
        try:
            # Set tenant context for RLS (Row Level Security)
            session.execute(f"SET app.current_tenant_id = '{tenant_id}'")
            yield session
        finally:
            session.close()

    def create_tables(self):
        """Create all database tables"""
        from laas.database.models import Base

        Base.metadata.create_all(bind=self.engine)

    def drop_tables(self):
        """Drop all database tables"""
        from laas.database.models import Base

        Base.metadata.drop_all(bind=self.engine)


# Global database manager instance
db_manager = DatabaseManager()


def get_db() -> Generator[Session, None, None]:
    """Dependency to get database session"""
    yield from db_manager.get_session()


def get_tenant_db(tenant_id: str) -> Generator[Session, None, None]:
    """Dependency to get tenant-specific database session"""
    yield from db_manager.get_tenant_session(tenant_id)


@asynccontextmanager
async def get_async_session():
    """Async context manager for database sessions"""
    session = db_manager.SessionLocal()
    try:
        yield session
    finally:
        session.close()

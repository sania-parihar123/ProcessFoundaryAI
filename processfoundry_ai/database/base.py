"""SQLAlchemy declarative base for ProcessFoundry AI models."""

from __future__ import annotations

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Base class for all SQLAlchemy ORM models.
    
    This class provides a shared metadata registry for all models,
    enabling Alembic to discover and manage table definitions.
    """

    pass

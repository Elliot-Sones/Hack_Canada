"""Read-only SQLAlchemy models for Better Auth tables.

These map to tables created by Better Auth in the same database.
NOT imported in __init__.py to keep them out of Alembic metadata.
"""

from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, String, Boolean
from sqlalchemy.orm import Mapped, mapped_column, DeclarativeBase


class BetterAuthBase(DeclarativeBase):
    """Separate base so these tables are never in Alembic's target_metadata."""
    pass


class BetterAuthUser(BetterAuthBase):
    __tablename__ = "user"
    __table_args__ = {"extend_existing": True}

    id: Mapped[str] = mapped_column(String, primary_key=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    email: Mapped[str] = mapped_column(String, nullable=False)
    email_verified: Mapped[bool] = mapped_column("emailVerified", Boolean, nullable=False, default=False)
    image: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime] = mapped_column("createdAt", DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column("updatedAt", DateTime(timezone=True), nullable=False)


class BetterAuthSession(BetterAuthBase):
    __tablename__ = "session"
    __table_args__ = {"extend_existing": True}

    id: Mapped[str] = mapped_column(String, primary_key=True)
    user_id: Mapped[str] = mapped_column("userId", String, nullable=False)
    token: Mapped[str] = mapped_column(String, nullable=False, unique=True)
    expires_at: Mapped[datetime] = mapped_column("expiresAt", DateTime(timezone=True), nullable=False)
    ip_address: Mapped[Optional[str]] = mapped_column("ipAddress", String, nullable=True)
    user_agent: Mapped[Optional[str]] = mapped_column("userAgent", String, nullable=True)
    created_at: Mapped[datetime] = mapped_column("createdAt", DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column("updatedAt", DateTime(timezone=True), nullable=False)

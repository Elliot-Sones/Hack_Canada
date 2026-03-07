import uuid
from collections.abc import AsyncGenerator

from fastapi import Depends, Header, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import async_session_factory


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


async def get_current_user(
    authorization: str | None = Header(None),
) -> dict:
    """Stub auth dependency. Returns a mock user. Raises 401 if no auth header."""
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing authorization header",
        )
    # TODO: Decode JWT and fetch real user
    return {
        "id": uuid.UUID("00000000-0000-0000-0000-000000000001"),
        "email": "dev@arterial.local",
        "organization_id": uuid.UUID("00000000-0000-0000-0000-000000000001"),
        "role": "admin",
    }


async def get_optional_idempotency_key(
    idempotency_key: str | None = Header(None, alias="Idempotency-Key"),
) -> str | None:
    return idempotency_key

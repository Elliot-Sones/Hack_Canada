import uuid
from collections.abc import AsyncGenerator

from fastapi import Depends, Header, HTTPException, status
from jose import JWTError, jwt
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import async_session_factory
from app.models.tenant import User, WorkspaceMember


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
    db: AsyncSession = Depends(get_db_session),
) -> dict:
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing authorization header",
        )

    scheme, _, token = authorization.partition(" ")
    if scheme.lower() != "bearer" or not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authorization header must use Bearer token format",
        )

    try:
        payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
    except JWTError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token") from exc

    subject = payload.get("sub") or payload.get("user_id")
    if not subject:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token is missing subject claim")

    try:
        user_id = uuid.UUID(str(subject))
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token subject must be a UUID") from exc

    org_claim = payload.get("organization_id") or payload.get("org_id")
    organization_id = None
    if org_claim is not None:
        try:
            organization_id = uuid.UUID(str(org_claim))
        except ValueError as exc:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token organization claim must be a UUID",
            ) from exc

    user_result = await db.execute(select(User).where(User.id == user_id, User.is_active.is_(True)))
    user = user_result.scalar_one_or_none()
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found or inactive")

    membership_query = select(WorkspaceMember).where(WorkspaceMember.user_id == user_id)
    if organization_id is not None:
        membership_query = membership_query.where(WorkspaceMember.organization_id == organization_id)
    membership_result = await db.execute(membership_query.order_by(WorkspaceMember.created_at.asc()))
    memberships = membership_result.scalars().all()
    if not memberships:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User has no workspace membership")

    if organization_id is None:
        if len(memberships) > 1:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Token must include organization_id when user belongs to multiple organizations",
            )
        membership = memberships[0]
    else:
        membership = memberships[0]

    return {
        "id": user.id,
        "email": user.email,
        "organization_id": membership.organization_id,
        "role": membership.role,
    }


async def get_optional_idempotency_key(
    idempotency_key: str | None = Header(None, alias="Idempotency-Key"),
) -> str | None:
    return idempotency_key

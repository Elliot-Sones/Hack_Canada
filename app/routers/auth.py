import os
import re
from datetime import datetime, timedelta, timezone

import structlog
from fastapi import APIRouter, Depends, HTTPException, status
from jose import jwt
from passlib.context import CryptContext
from sqlalchemy import select, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.dependencies import get_db_session
from app.models.better_auth import BetterAuthSession, BetterAuthUser
from app.models.tenant import Organization, User, WorkspaceMember
from app.schemas.auth import LoginRequest, RegisterRequest, SessionExchangeRequest, TokenResponse, UserInfo

log = structlog.get_logger()

router = APIRouter()

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def _slugify(name: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")
    return slug or "org"


def _create_token(user: User, organization_id) -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {
        "sub": str(user.id),
        "organization_id": str(organization_id),
        "exp": expire,
    }
    return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


@router.post("/auth/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register(body: RegisterRequest, db: AsyncSession = Depends(get_db_session)):
    existing = await db.execute(select(User).where(User.email == body.email))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already registered")

    org = Organization(name=body.organization_name, slug=_slugify(body.organization_name))
    db.add(org)
    await db.flush()

    user = User(email=body.email, name=body.name, password_hash=pwd_context.hash(body.password))
    db.add(user)
    await db.flush()

    member = WorkspaceMember(organization_id=org.id, user_id=user.id, role="owner")
    db.add(member)
    await db.flush()

    token = _create_token(user, org.id)
    return TokenResponse(
        access_token=token,
        user=UserInfo(id=str(user.id), email=user.email, name=user.name, organization_id=str(org.id)),
    )


@router.post("/auth/login", response_model=TokenResponse)
async def login(body: LoginRequest, db: AsyncSession = Depends(get_db_session)):
    result = await db.execute(select(User).where(User.email == body.email))
    user = result.scalar_one_or_none()
    if not user or not user.password_hash or not pwd_context.verify(body.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password")

    member_result = await db.execute(
        select(WorkspaceMember).where(WorkspaceMember.user_id == user.id).order_by(WorkspaceMember.created_at.asc())
    )
    member = member_result.scalar_one_or_none()
    if not member:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No workspace membership found")

    token = _create_token(user, member.organization_id)
    return TokenResponse(
        access_token=token,
        user=UserInfo(id=str(user.id), email=user.email, name=user.name, organization_id=str(member.organization_id)),
    )


@router.post("/auth/session-exchange", response_model=TokenResponse)
async def session_exchange(body: SessionExchangeRequest, db: AsyncSession = Depends(get_db_session)):
    """Exchange a Better Auth session token for a FastAPI JWT."""
    # 1. Look up the Better Auth session
    result = await db.execute(
        select(BetterAuthSession).where(BetterAuthSession.token == body.session_token)
    )
    ba_session = result.scalar_one_or_none()
    if not ba_session:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid session token")

    # 2. Check expiry
    if ba_session.expires_at < datetime.now(timezone.utc):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Session expired")

    # 3. Get the Better Auth user
    ba_user_result = await db.execute(
        select(BetterAuthUser).where(BetterAuthUser.id == ba_session.user_id)
    )
    ba_user = ba_user_result.scalar_one_or_none()
    if not ba_user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")

    # 4. Find or create the cocivil user by email
    user = await _find_or_create_cocivil_user(db, ba_user)

    # 5. Get workspace membership for org_id
    member_result = await db.execute(
        select(WorkspaceMember).where(WorkspaceMember.user_id == user.id).order_by(WorkspaceMember.created_at.asc())
    )
    member = member_result.scalar_one_or_none()
    if not member:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No workspace membership found")

    token = _create_token(user, member.organization_id)
    return TokenResponse(
        access_token=token,
        user=UserInfo(id=str(user.id), email=user.email, name=user.name, organization_id=str(member.organization_id)),
    )


async def _find_or_create_cocivil_user(db: AsyncSession, ba_user: BetterAuthUser) -> User:
    """Find existing cocivil user by email, or bootstrap a new one."""
    import uuid as _uuid
    from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession as _AS
    from sqlalchemy.ext.asyncio import async_sessionmaker
    from app.config import settings

    result = await db.execute(select(User).where(User.email == ba_user.email))
    user = result.scalar_one_or_none()
    if user:
        return user

    # First-time bootstrap: use a SEPARATE connection to avoid corrupting
    # the request's async session if IntegrityError + rollback occurs.
    engine = create_async_engine(settings.DATABASE_URL, echo=False)
    factory = async_sessionmaker(engine, class_=_AS, expire_on_commit=False)

    org_name = f"{ba_user.name}'s Organization"
    slug = _slugify(org_name)
    org_id = _uuid.uuid4()
    user_id = _uuid.uuid4()

    async with factory() as fresh_db:
        # Create org (skip if slug already exists from a prior partial bootstrap)
        existing_org = await fresh_db.execute(
            text("SELECT id FROM organizations WHERE slug = :slug"), {"slug": slug}
        )
        org_row = existing_org.first()
        if org_row:
            org_id = org_row[0]
        else:
            await fresh_db.execute(
                text("INSERT INTO organizations (id, name, slug) VALUES (:id, :name, :slug)"),
                {"id": str(org_id), "name": org_name, "slug": slug},
            )

        # Create user (skip if email already exists)
        existing_user = await fresh_db.execute(
            text("SELECT id FROM users WHERE email = :email"), {"email": ba_user.email}
        )
        user_row = existing_user.first()
        if user_row:
            user_id = user_row[0]
        else:
            await fresh_db.execute(
                text("INSERT INTO users (id, email, name) VALUES (:id, :email, :name)"),
                {"id": str(user_id), "email": ba_user.email, "name": ba_user.name},
            )

        # Create membership (skip if already exists)
        existing_member = await fresh_db.execute(
            text("SELECT 1 FROM workspace_members WHERE user_id = :uid"), {"uid": str(user_id)}
        )
        if not existing_member.first():
            await fresh_db.execute(
                text("INSERT INTO workspace_members (organization_id, user_id, role) VALUES (:org_id, :user_id, :role)"),
                {"org_id": str(org_id), "user_id": str(user_id), "role": "owner"},
            )

        await fresh_db.commit()

    await engine.dispose()

    log.info("bootstrapped_cocivil_user", email=ba_user.email, org_slug=slug)

    # Fetch the created user via the request's session
    result = await db.execute(select(User).where(User.id == user_id))
    return result.scalar_one()

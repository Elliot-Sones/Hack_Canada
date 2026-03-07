import re
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from jose import jwt
from passlib.context import CryptContext
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.dependencies import get_db_session
from app.models.tenant import Organization, User, WorkspaceMember
from app.schemas.auth import LoginRequest, RegisterRequest, TokenResponse, UserInfo

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

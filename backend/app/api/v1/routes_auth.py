import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from jose import jwt, JWTError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.deps import get_current_user
from app.core.config import settings
from app.core.security import (
    create_access_token,
    create_refresh_token,
    hash_password,
    verify_password,
)
from app.db.session import get_db
from app.models.models import RefreshToken, User
from app.schemas.schemas import (
    AccessTokenOut,
    RefreshRequest,
    Token,
    UserCreate,
    UserOut,
)

router = APIRouter(prefix="/auth", tags=["auth"])


async def _issue_token_pair(user: User, db: AsyncSession) -> Token:
    """Mints an access token plus a refresh token, persisting the refresh
    token's expiry so outstanding sessions can be enumerated/revoked (logout).
    """
    access_token = create_access_token(subject=str(user.id))
    refresh_token = create_refresh_token(subject=str(user.id))

    payload = jwt.get_unverified_claims(refresh_token)
    expires_at = datetime.fromtimestamp(payload["exp"], tz=timezone.utc)

    db.add(
        RefreshToken(
            user_id=user.id,
            jti=str(uuid.uuid4()),
            expires_at=expires_at,
        )
    )

    await db.commit()

    return Token(
        access_token=access_token,
        refresh_token=refresh_token,
    )


@router.post(
    "/register",
    response_model=UserOut,
    status_code=status.HTTP_201_CREATED,
)
async def register(
    payload: UserCreate,
    db: AsyncSession = Depends(get_db),
):
    # bcrypt has a maximum password length of 72 bytes.
    # We reject longer passwords instead of silently truncating them.
    password_bytes = len(payload.password.encode("utf-8"))

    if password_bytes > 72:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password must be 72 bytes or fewer.",
        )

    existing = await db.execute(
        select(User).where(User.email == payload.email)
    )

    if existing.scalar_one_or_none() is not None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )

    user = User(
        email=payload.email,
        hashed_password=hash_password(payload.password),
    )

    db.add(user)

    await db.commit()
    await db.refresh(user)

    return UserOut(
        id=str(user.id),
        email=user.email,
        created_at=user.created_at,
    )


@router.post("/login", response_model=Token)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(User).where(User.email == form_data.username)
    )

    user = result.scalar_one_or_none()

    if user is None or not verify_password(
        form_data.password,
        user.hashed_password,
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return await _issue_token_pair(user, db)


@router.post("/refresh", response_model=AccessTokenOut)
async def refresh_access_token(
    payload: RefreshRequest,
    db: AsyncSession = Depends(get_db),
):
    """Exchanges a valid refresh token for a new access token."""

    try:
        claims = jwt.decode(
            payload.refresh_token,
            settings.SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM],
        )

    except JWTError:
        raise HTTPException(
            status_code=401,
            detail="Invalid or expired refresh token",
        )

    if claims.get("type") != "refresh":
        raise HTTPException(
            status_code=401,
            detail="Token is not a refresh token",
        )

    user_id = claims.get("sub")

    try:
        parsed_id = uuid.UUID(user_id)

    except (TypeError, ValueError):
        raise HTTPException(
            status_code=401,
            detail="Invalid token subject",
        )

    result = await db.execute(
        select(User).where(User.id == parsed_id)
    )

    user = result.scalar_one_or_none()

    if user is None:
        raise HTTPException(
            status_code=401,
            detail="User no longer exists",
        )

    return AccessTokenOut(
        access_token=create_access_token(
            subject=str(user.id)
        )
    )


@router.post(
    "/logout",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def logout_all_sessions(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Revokes all of the current user's outstanding refresh tokens."""

    result = await db.execute(
        select(RefreshToken).where(
            RefreshToken.user_id == user.id,
            RefreshToken.revoked.is_(False),
        )
    )

    for token in result.scalars().all():
        token.revoked = True

    await db.commit()

import hashlib
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import generate_opaque_token, hash_password
from app.models.models import EmailDomain, EmailVerificationToken, User
from app.schemas.auth import (
    MessageResponse,
    RegisterRequest,
    RegisterResponse,
    VerifyEmailRequest,
)

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post(
    "/register",
    response_model=RegisterResponse,
    status_code=status.HTTP_201_CREATED,
)
async def register(
    payload: RegisterRequest,
    db: AsyncSession = Depends(get_db),
) -> RegisterResponse:
    email = str(payload.email).lower()
    domain = email.split("@", 1)[1]

    result = await db.execute(
        select(EmailDomain).where(
            EmailDomain.domain == domain,
            EmailDomain.is_active.is_(True),
        )
    )
    email_domain = result.scalar_one_or_none()
    if email_domain is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Your university is not yet on WajhUni.",
        )

    existing = await db.execute(select(User).where(User.email == email))
    if existing.scalar_one_or_none():
        return RegisterResponse(
            message="If this email is eligible, a verification link has been sent."
        )
    user = User(
        full_name=payload.full_name,
        email=email,
        password_hash=hash_password(payload.password),
        university_id=email_domain.university_id,
    )
    db.add(user)
    await db.flush()

    raw_token, token_hash = generate_opaque_token()
    db.add(
        EmailVerificationToken(
            user_id=user.id,
            token_hash=token_hash,
            expires_at=datetime.now(timezone.utc) + timedelta(hours=24),
        )
    )

    print(f"[DEV] verification token for {email}: {raw_token}")

    return RegisterResponse(
        message="If this email is eligible, a verification link has been sent."
    )


@router.post("/verify-email", response_model=MessageResponse)
async def verify_email(
    payload: VerifyEmailRequest,
    db: AsyncSession = Depends(get_db),
) -> MessageResponse:
    token_hash = hashlib.sha256(payload.token.encode()).hexdigest()
    now = datetime.now(timezone.utc)

    result = await db.execute(
        update(EmailVerificationToken)
        .where(
            EmailVerificationToken.token_hash == token_hash,
            EmailVerificationToken.used_at.is_(None),
            EmailVerificationToken.expires_at > now,
        )
        .values(used_at=now)
        .returning(EmailVerificationToken.user_id)
    )
    user_id = result.scalar_one_or_none()

    invalid = HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="This verification link is invalid or has expired.",
    )
    if user_id is None:
        raise invalid

    result = await db.execute(
        update(User)
        .where(User.id == user_id, User.verification_status == "pending")
        .values(verification_status="verified")
    )
    if result.rowcount == 0:
        raise invalid

    return MessageResponse(message="Email verified. You can now log in.")

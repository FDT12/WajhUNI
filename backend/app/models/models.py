import uuid
from datetime import datetime, timezone
from sqlalchemy import (
    String, Text, Boolean, SmallInteger,
    Numeric, ForeignKey, UniqueConstraint,
    CheckConstraint, DateTime, Index, func, text
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID
from app.core.database import Base


# ── helpers ──────────────────────────────────────────────────
def uuid_pk():
    return mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )

def now_utc():
    return mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        server_default=func.now(),
    )


# ── University ────────────────────────────────────────────────
class University(Base):
    __tablename__ = "universities"

    id:                 Mapped[uuid.UUID]       = uuid_pk()
    name_ar:            Mapped[str]             = mapped_column(String(255), nullable=False)
    name_fr:            Mapped[str]             = mapped_column(String(255), nullable=False)
    acronym:            Mapped[str]             = mapped_column(String(20), nullable=False, unique=True)
    type:               Mapped[str]             = mapped_column(String(50), nullable=False)
    governorate:        Mapped[str]             = mapped_column(String(100), nullable=False, default="Tunis")
    neighborhood:       Mapped[str | None]      = mapped_column(String(100))
    address:            Mapped[str | None]      = mapped_column(Text)
    latitude:           Mapped[float | None]    = mapped_column(Numeric(10, 7))
    longitude:          Mapped[float | None]    = mapped_column(Numeric(10, 7))
    nearest_transport:  Mapped[str | None]      = mapped_column(Text)
    website_url:        Mapped[str | None]      = mapped_column(String(500))
    description:        Mapped[str | None]      = mapped_column(Text)
    is_active:          Mapped[bool]            = mapped_column(Boolean, default=True, nullable=False)
    created_at:         Mapped[datetime]        = now_utc()

    # relationships
    email_domains:      Mapped[list["EmailDomain"]]         = relationship(back_populates="university")
    users:              Mapped[list["User"]]                = relationship(back_populates="university")
    submissions:        Mapped[list["RatingSubmission"]]    = relationship(back_populates="university")
    photos:             Mapped[list["UniversityPhoto"]]     = relationship(back_populates="university")

    __table_args__ = (
        CheckConstraint("type IN ('public', 'private', 'grandes_ecoles')", name="chk_university_type"),
        Index("idx_universities_type", "type"),
        Index("idx_universities_governorate", "governorate"),
        Index("idx_universities_is_active", "is_active"),
    )


# ── EmailDomain ───────────────────────────────────────────────
class EmailDomain(Base):
    __tablename__ = "email_domains"

    id:             Mapped[uuid.UUID]   = uuid_pk()
    university_id:  Mapped[uuid.UUID]   = mapped_column(ForeignKey("universities.id", ondelete="CASCADE"), nullable=False)
    domain:         Mapped[str]         = mapped_column(String(255), nullable=False, unique=True)
    is_active:      Mapped[bool]        = mapped_column(Boolean, default=True, nullable=False)

    university: Mapped["University"] = relationship(back_populates="email_domains")

    __table_args__ = (
        Index("idx_email_domains_domain", "domain"),
        Index("idx_email_domains_university", "university_id"),
    )


# ── User ──────────────────────────────────────────────────────
class User(Base):
    __tablename__ = "users"

    id:                  Mapped[uuid.UUID]      = uuid_pk()
    full_name:           Mapped[str]            = mapped_column(String(255), nullable=False)
    email:               Mapped[str]            = mapped_column(String(255), nullable=False, unique=True)
    password_hash:       Mapped[str]            = mapped_column(String(255), nullable=False)
    role:                Mapped[str]            = mapped_column(String(20), nullable=False, default="student")
    verification_status: Mapped[str]            = mapped_column(String(20), nullable=False, default="pending")
    university_id:       Mapped[uuid.UUID|None] = mapped_column(ForeignKey("universities.id", ondelete="SET NULL"))
    profile_picture_url: Mapped[str | None]     = mapped_column(String(500))
    created_at:          Mapped[datetime]       = now_utc()
    last_login:          Mapped[datetime|None]  = mapped_column(DateTime(timezone=True), nullable=True)

    university:     Mapped["University | None"]         = relationship(back_populates="users")
    submissions:    Mapped[list["RatingSubmission"]]    = relationship(back_populates="user")
    photos:         Mapped[list["UniversityPhoto"]]     = relationship(back_populates="uploaded_by_user")
    tokens:         Mapped[list["EmailVerificationToken"]] = relationship(back_populates="user")

    __table_args__ = (
        CheckConstraint("role IN ('student', 'admin')", name="chk_user_role"),
        CheckConstraint("verification_status IN ('pending', 'verified', 'suspended')", name="chk_user_status"),
    )


# ── EmailVerificationToken ────────────────────────────────────
class EmailVerificationToken(Base):
    __tablename__ = "email_verification_tokens"

    id:          Mapped[uuid.UUID]      = uuid_pk()
    user_id:     Mapped[uuid.UUID]      = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    token_hash:  Mapped[str]            = mapped_column(String(255), nullable=False, unique=True)
    expires_at:  Mapped[datetime]       = mapped_column(DateTime(timezone=True), nullable=False)
    used_at:     Mapped[datetime|None]  = mapped_column(DateTime(timezone=True), nullable=True)
    created_at:  Mapped[datetime]       = now_utc()

    user: Mapped["User"] = relationship(back_populates="tokens")

    __table_args__ = (
        Index("idx_verification_tokens_hash", "token_hash"),
        Index("idx_verification_tokens_user", "user_id"),
    )


# ── RatingCategory ────────────────────────────────────────────
class RatingCategory(Base):
    __tablename__ = "rating_categories"

    id:                Mapped[uuid.UUID]    = uuid_pk()
    name:              Mapped[str]          = mapped_column(String(100), nullable=False)
    slug:              Mapped[str]          = mapped_column(String(100), nullable=False, unique=True)
    headline_question: Mapped[str]          = mapped_column(Text, nullable=False)
    description:       Mapped[str | None]   = mapped_column(Text)
    display_order:     Mapped[int]          = mapped_column(SmallInteger, nullable=False, unique=True)
    is_active:         Mapped[bool]         = mapped_column(Boolean, default=True, nullable=False)

    sub_questions:  Mapped[list["RatingSubQuestion"]]   = relationship(back_populates="category")
    scores:         Mapped[list["RatingScore"]]         = relationship(back_populates="category")
    sub_scores:     Mapped[list["RatingSubScore"]]      = relationship(back_populates="category")
    comments:       Mapped[list["Comment"]]             = relationship(back_populates="category")


# ── RatingSubQuestion ─────────────────────────────────────────
class RatingSubQuestion(Base):
    __tablename__ = "rating_sub_questions"

    id:            Mapped[uuid.UUID]    = uuid_pk()
    category_id:   Mapped[uuid.UUID]    = mapped_column(ForeignKey("rating_categories.id", ondelete="CASCADE"), nullable=False)
    sub_key:       Mapped[str]          = mapped_column(String(100), nullable=False)
    question_text: Mapped[str]          = mapped_column(Text, nullable=False)
    display_order: Mapped[int]          = mapped_column(SmallInteger, nullable=False)

    category: Mapped["RatingCategory"] = relationship(back_populates="sub_questions")

    __table_args__ = (
        UniqueConstraint("category_id", "sub_key", name="uq_category_sub_key"),
    )


# ── RatingSubmission ──────────────────────────────────────────
class RatingSubmission(Base):
    __tablename__ = "rating_submissions"

    id:                Mapped[uuid.UUID]    = uuid_pk()
    user_id:           Mapped[uuid.UUID]    = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    university_id:     Mapped[uuid.UUID]    = mapped_column(ForeignKey("universities.id", ondelete="CASCADE"), nullable=False)
    moderation_status: Mapped[str]          = mapped_column(String(20), nullable=False, default="pending")
    is_anonymous:      Mapped[bool]         = mapped_column(Boolean, default=False, nullable=False)
    is_locked:         Mapped[bool]         = mapped_column(Boolean, default=False, nullable=False)
    lock_reason:       Mapped[str | None]   = mapped_column(String(50))
    created_at:        Mapped[datetime]     = now_utc()
    updated_at:        Mapped[datetime]     = now_utc()

    user:       Mapped["User"]                  = relationship(back_populates="submissions")
    university: Mapped["University"]            = relationship(back_populates="submissions")
    scores:     Mapped[list["RatingScore"]]     = relationship(back_populates="submission")
    sub_scores: Mapped[list["RatingSubScore"]]  = relationship(back_populates="submission")
    comments:   Mapped[list["Comment"]]         = relationship(back_populates="submission")

    __table_args__ = (
        UniqueConstraint("user_id", "university_id", name="uq_user_university"),
        CheckConstraint(
            "moderation_status IN ('pending', 'approved', 'flagged', 'rejected')",
            name="chk_submission_status"
        ),
        Index("idx_rating_submissions_university", "university_id"),
        Index("idx_rating_submissions_user", "user_id"),
        Index("idx_rating_submissions_status", "moderation_status"),
    )


# ── RatingScore ───────────────────────────────────────────────
class RatingScore(Base):
    __tablename__ = "rating_scores"

    id:            Mapped[uuid.UUID]    = uuid_pk()
    submission_id: Mapped[uuid.UUID]    = mapped_column(ForeignKey("rating_submissions.id", ondelete="CASCADE"), nullable=False)
    category_id:   Mapped[uuid.UUID]    = mapped_column(ForeignKey("rating_categories.id", ondelete="CASCADE"), nullable=False)
    score:         Mapped[int]          = mapped_column(SmallInteger, nullable=False)

    submission: Mapped["RatingSubmission"]  = relationship(back_populates="scores")
    category:   Mapped["RatingCategory"]   = relationship(back_populates="scores")

    __table_args__ = (
        UniqueConstraint("submission_id", "category_id", name="uq_score_submission_category"),
        CheckConstraint("score >= 1 AND score <= 5", name="chk_score_range"),
        Index("idx_rating_scores_submission", "submission_id"),
        Index("idx_rating_scores_category", "category_id"),
    )


# ── RatingSubScore ────────────────────────────────────────────
class RatingSubScore(Base):
    __tablename__ = "rating_sub_scores"

    id:            Mapped[uuid.UUID]    = uuid_pk()
    submission_id: Mapped[uuid.UUID]    = mapped_column(ForeignKey("rating_submissions.id", ondelete="CASCADE"), nullable=False)
    category_id:   Mapped[uuid.UUID]    = mapped_column(ForeignKey("rating_categories.id", ondelete="CASCADE"), nullable=False)
    sub_key:       Mapped[str]          = mapped_column(String(100), nullable=False)
    score:         Mapped[int]          = mapped_column(SmallInteger, nullable=False)

    submission: Mapped["RatingSubmission"]  = relationship(back_populates="sub_scores")
    category:   Mapped["RatingCategory"]   = relationship(back_populates="sub_scores")

    __table_args__ = (
        UniqueConstraint("submission_id", "category_id", "sub_key", name="uq_sub_score_unique"),
        CheckConstraint("score >= 1 AND score <= 5", name="chk_sub_score_range"),
    )


# ── Comment ───────────────────────────────────────────────────
class Comment(Base):
    __tablename__ = "comments"

    id:                Mapped[uuid.UUID]    = uuid_pk()
    submission_id:     Mapped[uuid.UUID]    = mapped_column(ForeignKey("rating_submissions.id", ondelete="CASCADE"), nullable=False)
    category_id:       Mapped[uuid.UUID]    = mapped_column(ForeignKey("rating_categories.id", ondelete="CASCADE"), nullable=False)
    body:              Mapped[str]          = mapped_column(Text, nullable=False)
    comment_prompt:    Mapped[str | None]   = mapped_column(Text)
    is_featured:       Mapped[bool]         = mapped_column(Boolean, default=False, nullable=False)
    is_anonymous:      Mapped[bool]         = mapped_column(Boolean, default=False, nullable=False)
    moderation_status: Mapped[str]          = mapped_column(String(20), nullable=False, default="pending")
    created_at:        Mapped[datetime]     = now_utc()

    submission: Mapped["RatingSubmission"]  = relationship(back_populates="comments")
    category:   Mapped["RatingCategory"]   = relationship(back_populates="comments")

    __table_args__ = (
        UniqueConstraint("submission_id", "category_id", name="uq_comment_submission_category"),
        CheckConstraint("char_length(body) <= 280", name="chk_comment_length"),
        CheckConstraint(
            "moderation_status IN ('pending', 'approved', 'flagged', 'rejected')",
            name="chk_comment_status"
        ),
        Index("idx_comments_submission", "submission_id"),
        Index("idx_comments_status", "moderation_status"),
        Index(
            "idx_comments_featured",
            "is_featured",
            postgresql_where=text("is_featured = true"),
        ),
    )


# ── UniversityPhoto ───────────────────────────────────────────
class UniversityPhoto(Base):
    __tablename__ = "university_photos"

    id:            Mapped[uuid.UUID]    = uuid_pk()
    university_id: Mapped[uuid.UUID]    = mapped_column(ForeignKey("universities.id", ondelete="CASCADE"), nullable=False)
    uploaded_by:   Mapped[uuid.UUID|None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"))
    url:           Mapped[str]          = mapped_column(String(1000), nullable=False)
    caption:       Mapped[str | None]   = mapped_column(String(255))
    category:      Mapped[str]          = mapped_column(String(50), nullable=False, default="campus")
    is_approved:   Mapped[bool]         = mapped_column(Boolean, default=False, nullable=False)
    display_order: Mapped[int | None]   = mapped_column(SmallInteger)
    created_at:    Mapped[datetime]     = now_utc()

    university:       Mapped["University"]      = relationship(back_populates="photos")
    uploaded_by_user: Mapped["User | None"]     = relationship(back_populates="photos")

    __table_args__ = (
        CheckConstraint(
            "category IN ('campus', 'library', 'sports', 'canteen', 'other')",
            name="chk_photo_category"
        ),
        Index("idx_photos_university", "university_id"),
        Index(
            "idx_photos_approved",
            "is_approved",
            postgresql_where=text("is_approved = true"),
        ),
    )
from datetime import datetime, timezone

from sqlalchemy import (
    ARRAY,
    JSON,
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Image(Base):
    __tablename__ = "images"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    filename: Mapped[str] = mapped_column(String, unique=True, index=True)
    url: Mapped[str | None] = mapped_column(String, nullable=True)

    subject: Mapped[str] = mapped_column(String)
    category: Mapped[str] = mapped_column(String)
    attributes: Mapped[list] = mapped_column(JSON, default=list)
    caption: Mapped[str] = mapped_column(Text)
    confidence: Mapped[float] = mapped_column(Float)

    embedding: Mapped[list] = mapped_column(ARRAY(Float), nullable=True)

    is_flagged: Mapped[bool] = mapped_column(Boolean, default=False)
    processed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    cost_micro: Mapped[int] = mapped_column(Integer, default=0)

    __table_args__ = (Index("ix_images_category", "category"),
                       Index("ix_images_is_flagged", "is_flagged"))


class Post(Base):
    __tablename__ = "posts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String)
    content: Mapped[str] = mapped_column(Text)
    embedding: Mapped[list] = mapped_column(ARRAY(Float), nullable=True)


class ImageSuggestion(Base):
    __tablename__ = "image_suggestions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    post_id: Mapped[int] = mapped_column(ForeignKey("posts.id"))
    image_id: Mapped[int] = mapped_column(ForeignKey("images.id"))
    similarity_score: Mapped[float] = mapped_column(Float)
    guard_passed: Mapped[bool] = mapped_column(Boolean)
    rejection_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String, default="pending")  # pending/approved/rejected
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    __table_args__ = (Index("ix_suggestions_post_id", "post_id"),
                       Index("ix_suggestions_status", "status"))


class VisionJobLog(Base):
    __tablename__ = "vision_job_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    image_id: Mapped[int | None] = mapped_column(ForeignKey("images.id"), nullable=True)
    filename: Mapped[str | None] = mapped_column(String, nullable=True)
    attempt: Mapped[int] = mapped_column(Integer, default=1)
    status: Mapped[str] = mapped_column(String)  # success/failed/flagged
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    cost_micro: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

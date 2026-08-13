from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.user import utcnow


class Comment(Base):
    __tablename__ = "comments"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    author_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    prompt_id: Mapped[int | None] = mapped_column(ForeignKey("prompts.id"), index=True, nullable=True)
    request_id: Mapped[int | None] = mapped_column(
        ForeignKey("requests.id"), index=True, nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    author = relationship("User", back_populates="comments")
    prompt = relationship("Prompt", back_populates="comments")
    request = relationship("Request", back_populates="comments")

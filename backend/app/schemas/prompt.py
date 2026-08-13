from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.schemas.user import UserOut


class PromptCreate(BaseModel):
    title: str = Field(min_length=3, max_length=150)
    description: str = Field(default="", max_length=300)
    content: str = Field(min_length=3)
    tags: list[str] = Field(default_factory=list, max_length=15)
    is_published: bool = True


class PromptUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=3, max_length=150)
    description: str | None = Field(default=None, max_length=300)
    content: str | None = Field(default=None, min_length=3)
    tags: list[str] | None = Field(default=None, max_length=15)
    is_published: bool | None = None


class CommentCreate(BaseModel):
    content: str = Field(min_length=1, max_length=2000)


class CommentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    content: str
    author: UserOut
    created_at: datetime


class PromptOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    description: str
    content: str
    tags: list[str]
    is_published: bool
    author: UserOut
    vote_score: int
    created_at: datetime
    updated_at: datetime

    @field_validator("tags", mode="before")
    @classmethod
    def split_tags(cls, value):
        if isinstance(value, str):
            return [t.strip() for t in value.split(",") if t.strip()]
        return value or []


class PromptList(BaseModel):
    items: list[PromptOut]
    total: int
    page: int
    size: int


class VoteIn(BaseModel):
    value: int = Field(default=1, ge=-1, le=1)

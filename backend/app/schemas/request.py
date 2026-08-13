from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.prompt import CommentOut
from app.schemas.user import UserOut


class RequestCreate(BaseModel):
    title: str = Field(min_length=3, max_length=150)
    description: str = Field(min_length=3)


class RequestUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=3, max_length=150)
    description: str | None = Field(default=None, min_length=3)
    status: str | None = Field(default=None, pattern="^(open|answered|closed)$")


class RequestOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    description: str
    status: str
    author: UserOut
    created_at: datetime
    updated_at: datetime


class RequestDetail(RequestOut):
    comments: list[CommentOut] = []


class RequestList(BaseModel):
    items: list[RequestOut]
    total: int
    page: int
    size: int

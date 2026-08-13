from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.models.comment import Comment
from app.models.request import Request
from app.schemas.request import RequestCreate, RequestUpdate


def create_request(db: Session, data: RequestCreate, author_id: int) -> Request:
    request = Request(
        title=data.title,
        description=data.description,
        status="open",
        author_id=author_id,
    )
    db.add(request)
    db.commit()
    db.refresh(request)
    return request


def get_request(db: Session, request_id: int) -> Request | None:
    return db.get(Request, request_id)


def list_requests(
    db: Session,
    skip: int = 0,
    limit: int = 20,
    status: str = "",
    search: str = "",
) -> tuple[list[Request], int]:
    filters = []
    if status:
        filters.append(Request.status == status)
    if search:
        like = f"%{search}%"
        filters.append(
            or_(Request.title.ilike(like), Request.description.ilike(like))
        )

    base = select(Request).where(*filters)
    total = db.scalar(select(func.count()).select_from(base.subquery())) or 0
    items = list(
        db.scalars(base.order_by(Request.created_at.desc()).offset(skip).limit(limit))
    )
    return items, total


def update_request(db: Session, request: Request, data: RequestUpdate) -> Request:
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(request, key, value)
    db.add(request)
    db.commit()
    db.refresh(request)
    return request


def delete_request(db: Session, request: Request) -> None:
    db.delete(request)
    db.commit()


def add_comment(
    db: Session, author_id: int, content: str, request_id: int | None = None
) -> Comment:
    comment = Comment(content=content, author_id=author_id, request_id=request_id)
    db.add(comment)
    db.commit()
    db.refresh(comment)
    return comment


def list_request_comments(db: Session, request_id: int) -> list[Comment]:
    return list(
        db.scalars(
            select(Comment)
            .where(Comment.request_id == request_id)
            .order_by(Comment.created_at.asc())
        )
    )


def count_requests(db: Session) -> int:
    return db.scalar(select(func.count()).select_from(Request)) or 0

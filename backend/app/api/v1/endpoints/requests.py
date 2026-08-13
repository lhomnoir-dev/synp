from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.database import get_db
from app.crud import crud_request
from app.models.request import Request
from app.models.user import User
from app.schemas.prompt import CommentCreate, CommentOut
from app.schemas.request import RequestCreate, RequestDetail, RequestList, RequestOut, RequestUpdate

router = APIRouter(prefix="/requests", tags=["requests"])


@router.post("", response_model=RequestOut, status_code=status.HTTP_201_CREATED)
def create_request(
    data: RequestCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return crud_request.create_request(db, data, current_user.id)


@router.get("", response_model=RequestList)
def list_requests(
    skip: int = 0,
    limit: int = 20,
    status_filter: str = "",
    search: str = "",
    db: Session = Depends(get_db),
):
    items, total = crud_request.list_requests(
        db, skip=skip, limit=limit, status=status_filter, search=search
    )
    return RequestList(items=items, total=total, page=skip // limit if limit else 0, size=limit)


@router.get("/{request_id}", response_model=RequestDetail)
def get_request(request_id: int, db: Session = Depends(get_db)):
    request = crud_request.get_request(db, request_id)
    if not request:
        raise HTTPException(status_code=404, detail="Demande introuvable")
    detail = RequestDetail.model_validate(request)
    detail.comments = crud_request.list_request_comments(db, request_id)
    return detail


@router.put("/{request_id}", response_model=RequestOut)
def update_request(
    request_id: int,
    data: RequestUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    request = _get_owned_request(db, request_id, current_user)
    return crud_request.update_request(db, request, data)


@router.delete("/{request_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_request(
    request_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    request = _get_owned_request(db, request_id, current_user)
    crud_request.delete_request(db, request)


@router.post("/{request_id}/comments", response_model=CommentOut, status_code=status.HTTP_201_CREATED)
def add_comment(
    request_id: int,
    data: CommentCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if not crud_request.get_request(db, request_id):
        raise HTTPException(status_code=404, detail="Demande introuvable")
    return crud_request.add_comment(
        db, current_user.id, data.content, request_id=request_id
    )


def _get_owned_request(db: Session, request_id: int, user: User) -> Request:
    request = crud_request.get_request(db, request_id)
    if not request:
        raise HTTPException(status_code=404, detail="Demande introuvable")
    if request.author_id != user.id and not user.is_admin:
        raise HTTPException(
            status_code=403, detail="Vous n'êtes pas propriétaire de cette demande"
        )
    return request

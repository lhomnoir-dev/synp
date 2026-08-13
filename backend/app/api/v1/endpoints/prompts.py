from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.database import get_db
from app.crud import crud_prompt
from app.models.user import User
from app.models.prompt import Prompt
from app.schemas.prompt import (
    CommentCreate,
    CommentOut,
    PromptCreate,
    PromptList,
    PromptOut,
    PromptUpdate,
    VoteIn,
)
from app.services.moderation import ModerationError, moderate, sanitize

router = APIRouter(prefix="/prompts", tags=["prompts"])


@router.post("", response_model=PromptOut, status_code=201)
def create_prompt(
    data: PromptCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    try:
        moderate(data.content)
        moderate(data.title)
    except ModerationError as exc:
        raise HTTPException(status_code=422, detail=exc.reason)
    return crud_prompt.create_prompt(db, data, current_user.id)


@router.get("", response_model=PromptList)
def list_prompts(
    skip: int = 0,
    limit: int = 20,
    search: str = "",
    tag: str = "",
    author_id: int | None = None,
    db: Session = Depends(get_db),
):
    items, total = crud_prompt.list_prompts(
        db, skip=skip, limit=limit, search=search, tag=tag, author_id=author_id
    )
    return PromptList(items=items, total=total, page=skip // limit if limit else 0, size=limit)


@router.get("/{prompt_id}", response_model=PromptOut)
def get_prompt(prompt_id: int, db: Session = Depends(get_db)):
    prompt = crud_prompt.get_prompt(db, prompt_id)
    if not prompt:
        raise HTTPException(status_code=404, detail="Prompt introuvable")
    return prompt


@router.put("/{prompt_id}", response_model=PromptOut)
def update_prompt(
    prompt_id: int,
    data: PromptUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    prompt = _get_owned_prompt(db, prompt_id, current_user)
    return crud_prompt.update_prompt(db, prompt, data)


@router.delete("/{prompt_id}", status_code=204)
def delete_prompt(
    prompt_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    prompt = _get_owned_prompt(db, prompt_id, current_user)
    crud_prompt.delete_prompt(db, prompt)


@router.post("/{prompt_id}/vote", response_model=PromptOut)
def vote_prompt(
    prompt_id: int,
    data: VoteIn,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    prompt = crud_prompt.get_prompt(db, prompt_id)
    if not prompt:
        raise HTTPException(status_code=404, detail="Prompt introuvable")
    crud_prompt.set_vote(db, current_user.id, prompt_id, data.value)
    return crud_prompt.get_prompt(db, prompt_id)


@router.delete("/{prompt_id}/vote", response_model=PromptOut)
def unvote_prompt(
    prompt_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    crud_prompt.remove_vote(db, current_user.id, prompt_id)
    return crud_prompt.get_prompt(db, prompt_id)


@router.get("/{prompt_id}/comments", response_model=list[CommentOut])
def list_comments(prompt_id: int, db: Session = Depends(get_db)):
    return crud_prompt.list_prompt_comments(db, prompt_id)


@router.post("/{prompt_id}/comments", response_model=CommentOut, status_code=201)
def add_comment(
    prompt_id: int,
    data: CommentCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if not crud_prompt.get_prompt(db, prompt_id):
        raise HTTPException(status_code=404, detail="Prompt introuvable")
    try:
        moderate(data.content)
    except ModerationError as exc:
        raise HTTPException(status_code=422, detail=exc.reason)
    return crud_prompt.add_comment(db, current_user.id, sanitize(data.content), prompt_id=prompt_id)


def _get_owned_prompt(db: Session, prompt_id: int, user: User) -> Prompt:
    prompt = crud_prompt.get_prompt(db, prompt_id)
    if not prompt:
        raise HTTPException(status_code=404, detail="Prompt introuvable")
    if prompt.author_id != user.id and not user.is_admin:
        raise HTTPException(status_code=403, detail="Vous n'êtes pas propriétaire de ce prompt")
    return prompt

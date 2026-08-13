from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.deps import get_current_admin
from app.core.database import get_db
from app.crud import crud_prompt, crud_request, crud_user
from app.models.comment import Comment
from app.models.prompt import Prompt
from app.models.request import Request
from app.models.user import User
from app.schemas.prompt import PromptOut

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/stats")
def get_stats(_: User = Depends(get_current_admin), db: Session = Depends(get_db)):
    return {
        "users": db.scalar(select(func.count()).select_from(User)) or 0,
        "prompts": crud_prompt.count_prompts(db),
        "requests": crud_request.count_requests(db),
        "comments": db.scalar(select(func.count()).select_from(Comment)) or 0,
    }


@router.get("/moderation/queue")
def moderation_queue(
    _: User = Depends(get_current_admin), db: Session = Depends(get_db)
):
    drafts = list(
        db.scalars(select(Prompt).where(Prompt.is_published.is_(False)))
    )
    return [PromptOut.model_validate(p) for p in drafts]


@router.post("/moderation/prompts/{prompt_id}/approve")
def approve_prompt(
    prompt_id: int,
    _: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    prompt = crud_prompt.get_prompt(db, prompt_id)
    if not prompt:
        raise HTTPException(status_code=404, detail="Prompt introuvable")
    prompt.is_published = True
    db.add(prompt)
    db.commit()
    return PromptOut.model_validate(prompt)


@router.delete("/moderation/prompts/{prompt_id}")
def delete_prompt_admin(
    prompt_id: int,
    _: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    prompt = crud_prompt.get_prompt(db, prompt_id)
    if not prompt:
        raise HTTPException(status_code=404, detail="Prompt introuvable")
    crud_prompt.delete_prompt(db, prompt)
    return {"detail": "Prompt supprimé"}


@router.get("/users")
def list_all_users(
    _: User = Depends(get_current_admin), db: Session = Depends(get_db)
):
    users = crud_user.get_users(db, limit=10000)
    return [
        {
            "id": u.id,
            "email": u.email,
            "username": u.username,
            "is_admin": u.is_admin,
            "is_active": u.is_active,
            "created_at": u.created_at,
            "prompts": len(u.prompts),
        }
        for u in users
    ]


@router.put("/users/{user_id}/toggle-admin")
def toggle_admin(
    user_id: int,
    _: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    user = crud_user.get_user(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="Utilisateur introuvable")
    if user.is_admin:
        raise HTTPException(status_code=400, detail="Impossible de rétrograder un admin")
    user.is_admin = True
    db.add(user)
    db.commit()
    return {"detail": "Utilisateur promu administrateur"}

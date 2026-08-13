from sqlalchemy import and_, func, or_, select
from sqlalchemy.orm import Session

from app.models.comment import Comment
from app.models.prompt import Prompt, Vote
from app.models.user import User
from app.schemas.prompt import PromptCreate, PromptUpdate


def create_prompt(db: Session, data: PromptCreate, author_id: int) -> Prompt:
    prompt = Prompt(
        title=data.title,
        description=data.description,
        content=data.content,
        tags=",".join(data.tags),
        is_published=data.is_published,
        author_id=author_id,
    )
    db.add(prompt)
    db.commit()
    db.refresh(prompt)
    return prompt


def get_prompt(db: Session, prompt_id: int) -> Prompt | None:
    return db.get(Prompt, prompt_id)


def list_prompts(
    db: Session,
    skip: int = 0,
    limit: int = 20,
    search: str = "",
    tag: str = "",
    author_id: int | None = None,
    published_only: bool = True,
) -> tuple[list[Prompt], int]:
    filters = []
    if published_only:
        filters.append(Prompt.is_published.is_(True))
    if author_id is not None:
        filters.append(Prompt.author_id == author_id)
    if tag:
        filters.append(Prompt.tags.ilike(f"%{tag}%"))
    if search:
        like = f"%{search}%"
        filters.append(or_(Prompt.title.ilike(like), Prompt.description.ilike(like)))

    base = select(Prompt).where(and_(*filters))
    total = db.scalar(select(func.count()).select_from(base.subquery())) or 0
    items = list(
        db.scalars(
            base.order_by(Prompt.created_at.desc()).offset(skip).limit(limit)
        )
    )
    return items, total


def update_prompt(db: Session, prompt: Prompt, data: PromptUpdate) -> Prompt:
    updates = data.model_dump(exclude_unset=True)
    if "tags" in updates and updates["tags"] is not None:
        updates["tags"] = ",".join(updates["tags"])
    for key, value in updates.items():
        setattr(prompt, key, value)
    db.add(prompt)
    db.commit()
    db.refresh(prompt)
    return prompt


def delete_prompt(db: Session, prompt: Prompt) -> None:
    db.delete(prompt)
    db.commit()


def count_prompts(db: Session) -> int:
    return db.scalar(select(func.count()).select_from(Prompt)) or 0


def get_user_vote(db: Session, user_id: int, prompt_id: int) -> Vote | None:
    return db.scalar(
        select(Vote).where(Vote.user_id == user_id, Vote.prompt_id == prompt_id)
    )


def set_vote(db: Session, user_id: int, prompt_id: int, value: int) -> Vote:
    vote = get_user_vote(db, user_id, prompt_id)
    if vote is None:
        vote = Vote(user_id=user_id, prompt_id=prompt_id, value=value)
        db.add(vote)
    else:
        vote.value = value
    db.commit()
    db.refresh(vote)
    return vote


def remove_vote(db: Session, user_id: int, prompt_id: int) -> None:
    vote = get_user_vote(db, user_id, prompt_id)
    if vote:
        db.delete(vote)
        db.commit()


def add_comment(
    db: Session, author_id: int, content: str, prompt_id: int | None = None,
    request_id: int | None = None,
) -> Comment:
    comment = Comment(
        content=content,
        author_id=author_id,
        prompt_id=prompt_id,
        request_id=request_id,
    )
    db.add(comment)
    db.commit()
    db.refresh(comment)
    return comment


def list_prompt_comments(db: Session, prompt_id: int) -> list[Comment]:
    return list(
        db.scalars(
            select(Comment)
            .where(Comment.prompt_id == prompt_id)
            .order_by(Comment.created_at.desc())
        )
    )


def list_prompt_author_usernames(db: Session, prompt: Prompt) -> User:
    return prompt.author

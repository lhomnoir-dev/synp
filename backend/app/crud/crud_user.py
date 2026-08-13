import json

from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.core.security import hash_password, verify_password
from app.models.user import User
from app.schemas.user import UserCreate, UserUpdate


def get_user(db: Session, user_id: int) -> User | None:
    return db.get(User, user_id)


def get_user_by_email(db: Session, email: str) -> User | None:
    return db.scalar(select(User).where(User.email == email))


def get_user_by_username(db: Session, username: str) -> User | None:
    return db.scalar(select(User).where(User.username == username))


def get_users(db: Session, skip: int = 0, limit: int = 50) -> list[User]:
    return list(db.scalars(select(User).offset(skip).limit(limit)))


def authenticate_user(db: Session, email: str, password: str) -> User | None:
    user = get_user_by_email(db, email)
    if not user or not verify_password(password, user.hashed_password):
        return None
    return user


def create_user(db: Session, data: UserCreate) -> User:
    user = User(
        email=data.email,
        username=data.username,
        bio=data.bio,
        hashed_password=hash_password(data.password),
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def update_user(db: Session, user: User, data: UserUpdate) -> User:
    if data.username is not None:
        user.username = data.username
    if data.bio is not None:
        user.bio = data.bio
    if data.password is not None:
        user.hashed_password = hash_password(data.password)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def save_api_key(db: Session, user: User, provider: str, encrypted_key: str) -> None:
    keys = json.loads(user.encrypted_api_keys or "{}")
    keys[provider] = encrypted_key
    user.encrypted_api_keys = json.dumps(keys)
    db.add(user)
    db.commit()


def get_api_key(db: Session, user: User, provider: str) -> str | None:
    keys = json.loads(user.encrypted_api_keys or "{}")
    return keys.get(provider)


def has_api_key(user: User, provider: str) -> bool:
    keys = json.loads(user.encrypted_api_keys or "{}")
    return provider in keys


def delete_api_key(db: Session, user: User, provider: str) -> None:
    keys = json.loads(user.encrypted_api_keys or "{}")
    keys.pop(provider, None)
    user.encrypted_api_keys = json.dumps(keys)
    db.add(user)
    db.commit()


def list_configured_providers(user: User) -> list[str]:
    return list(json.loads(user.encrypted_api_keys or "{}").keys())


def search_users(db: Session, query: str, skip: int = 0, limit: int = 50) -> list[User]:
    like = f"%{query}%"
    stmt = (
        select(User)
        .where(or_(User.username.ilike(like), User.email.ilike(like)))
        .offset(skip)
        .limit(limit)
    )
    return list(db.scalars(stmt))

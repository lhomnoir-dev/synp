from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import get_current_admin, get_current_user
from app.core.database import get_db
from app.core.encryption import decrypt_secret, encrypt_secret
from app.crud import crud_user
from app.models.user import User
from app.schemas.user import ApiKeyIn, ApiKeyOut, UserOut, UserUpdate

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me", response_model=UserOut)
def read_me(current_user: User = Depends(get_current_user)):
    return current_user


@router.put("/me", response_model=UserOut)
def update_me(
    data: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return crud_user.update_user(db, current_user, data)


@router.put("/me/api-keys/{provider}", response_model=ApiKeyOut)
def set_api_key(
    provider: str,
    data: ApiKeyIn,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    encrypted = encrypt_secret(data.api_key)
    crud_user.save_api_key(db, current_user, data.provider, encrypted)
    return ApiKeyOut(provider=data.provider, configured=True)


@router.get("/me/api-keys", response_model=list[ApiKeyOut])
def list_api_keys(current_user: User = Depends(get_current_user)):
    return [
        ApiKeyOut(provider=provider, configured=True)
        for provider in crud_user.list_configured_providers(current_user)
    ]


@router.delete("/me/api-keys/{provider}", response_model=ApiKeyOut)
def remove_api_key(
    provider: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    crud_user.delete_api_key(db, current_user, provider)
    return ApiKeyOut(provider=provider, configured=False)


@router.get("", response_model=list[UserOut])
def list_users(
    skip: int = 0,
    limit: int = 50,
    search: str = "",
    _: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    if search:
        return crud_user.search_users(db, search, skip, limit)
    return crud_user.get_users(db, skip, limit)


@router.get("/{user_id}", response_model=UserOut)
def read_user(user_id: int, db: Session = Depends(get_db)):
    user = crud_user.get_user(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="Utilisateur introuvable")
    return user

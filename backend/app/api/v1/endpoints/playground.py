import json

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.database import get_db
from app.core.encryption import decrypt_secret
from app.crud import crud_user
from app.models.user import User
from app.schemas.token import PlaygroundRequest, PlaygroundResponse
from app.services.llm_service import DEFAULT_MODELS, LLMService, LLMServiceError

router = APIRouter(prefix="/playground", tags=["playground"])


def _build_service(user: User, provider: str) -> LLMService:
    encrypted = crud_user.get_api_key(user, provider)
    if not encrypted:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Aucune clé API configurée pour {provider}. "
            "Ajoutez-la via PUT /api/v1/users/me/api-keys/{provider}.",
        )
    return LLMService(decrypt_secret(encrypted), provider)


def _safe_model(provider: str, model: str) -> str:
    return model or DEFAULT_MODELS.get(provider, "")


@router.post("", response_model=PlaygroundResponse)
async def run_playground(
    data: PlaygroundRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    service = _build_service(current_user, data.provider)
    try:
        output, usage = await service.complete(
            prompt=data.prompt,
            model=_safe_model(data.provider, data.model),
            system_prompt=data.system_prompt,
            temperature=data.temperature,
            max_tokens=data.max_tokens,
        )
    except LLMServiceError as exc:
        raise HTTPException(status_code=502, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Erreur du provider : {exc}")
    return PlaygroundResponse(
        provider=data.provider,
        model=_safe_model(data.provider, data.model),
        output=output,
        usage=usage,
    )


@router.post("/stream")
async def stream_playground(
    data: PlaygroundRequest,
    current_user: User = Depends(get_current_user),
):
    if not data.stream:
        raise HTTPException(status_code=400, detail="Activez stream=true")
    service = _build_service(current_user, data.provider)

    async def event_generator():
        try:
            async for chunk in service.stream(
                prompt=data.prompt,
                model=_safe_model(data.provider, data.model),
                system_prompt=data.system_prompt,
                temperature=data.temperature,
                max_tokens=data.max_tokens,
            ):
                yield f"data: {json.dumps({'chunk': chunk}, ensure_ascii=False)}\n\n"
            yield "data: [DONE]\n\n"
        except Exception as exc:
            yield f"event: error\ndata: {json.dumps({'detail': str(exc)})}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )

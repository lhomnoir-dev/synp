from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.router import router as api_v1_router
from app.core.config import settings

app = FastAPI(
    title=settings.project_name,
    version=settings.project_version,
    description="API REST de PromptHub : partage de prompts, votes, forum d'entraide et test direct de LLM.",
    openapi_url=f"{settings.api_v1_prefix}/openapi.json",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_v1_router, prefix=settings.api_v1_prefix)


@app.get("/", tags=["health"])
def root():
    return {"app": settings.project_name, "version": settings.project_version, "docs": "/docs"}


@app.get("/health", tags=["health"])
def health():
    return {"status": "ok"}

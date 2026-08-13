from fastapi import APIRouter

from app.api.v1.endpoints import admin, auth, playground, prompts, requests, users

router = APIRouter()

router.include_router(auth.router)
router.include_router(users.router)
router.include_router(prompts.router)
router.include_router(requests.router)
router.include_router(playground.router)
router.include_router(admin.router)

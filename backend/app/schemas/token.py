from pydantic import BaseModel, EmailStr, Field

from app.schemas.user import UserOut


class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: UserOut


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class RefreshRequest(BaseModel):
    refresh_token: str


class PlaygroundRequest(BaseModel):
    provider: str = Field(pattern="^(openai|anthropic|gemini)$")
    model: str = Field(default="", max_length=100)
    prompt: str = Field(min_length=1)
    system_prompt: str = Field(default="", max_length=2000)
    temperature: float = Field(default=0.7, ge=0.0, le=2.0)
    max_tokens: int = Field(default=1024, ge=1, le=8192)
    stream: bool = False


class PlaygroundResponse(BaseModel):
    provider: str
    model: str
    output: str
    usage: dict = {}

import json
from typing import Any, AsyncIterator

import httpx

from app.core.config import settings

DEFAULT_MODELS = {
    "openai": "gpt-4o-mini",
    "anthropic": "claude-3-5-haiku-latest",
    "gemini": "gemini-1.5-flash",
}


class LLMServiceError(Exception):
    pass


class LLMService:
    def __init__(self, api_key: str, provider: str):
        self.provider = provider
        self.api_key = api_key

    @property
    def default_model(self) -> str:
        return DEFAULT_MODELS.get(self.provider, "")

    async def complete(
        self,
        prompt: str,
        model: str = "",
        system_prompt: str = "",
        temperature: float = 0.7,
        max_tokens: int = 1024,
    ) -> tuple[str, dict[str, Any]]:
        model = model or self.default_model
        if self.provider == "openai":
            return await self._complete_openai(prompt, model, system_prompt, temperature, max_tokens)
        if self.provider == "anthropic":
            return await self._complete_anthropic(prompt, model, system_prompt, temperature, max_tokens)
        if self.provider == "gemini":
            return await self._complete_gemini(prompt, model, system_prompt, temperature, max_tokens)
        raise LLMServiceError(f"Provider inconnu : {self.provider}")

    async def stream(
        self,
        prompt: str,
        model: str = "",
        system_prompt: str = "",
        temperature: float = 0.7,
        max_tokens: int = 1024,
    ) -> AsyncIterator[str]:
        model = model or self.default_model
        if self.provider == "openai":
            async for chunk in self._stream_openai(prompt, model, system_prompt, temperature, max_tokens):
                yield chunk
        elif self.provider == "anthropic":
            async for chunk in self._stream_anthropic(prompt, model, system_prompt, temperature, max_tokens):
                yield chunk
        elif self.provider == "gemini":
            async for chunk in self._stream_gemini(prompt, model, system_prompt, temperature, max_tokens):
                yield chunk
        else:
            raise LLMServiceError(f"Provider inconnu : {self.provider}")

    # --- OpenAI ---
    async def _complete_openai(self, prompt, model, system_prompt, temperature, max_tokens):
        messages = self._messages(prompt, system_prompt)
        async with httpx.AsyncClient(timeout=60) as client:
            resp = await client.post(
                "https://api.openai.com/v1/chat/completions",
                headers={"Authorization": f"Bearer {self.api_key}"},
                json={
                    "model": model,
                    "messages": messages,
                    "temperature": temperature,
                    "max_tokens": max_tokens,
                },
            )
            resp.raise_for_status()
            data = resp.json()
        return data["choices"][0]["message"]["content"], {
            "model": data.get("model"),
            "usage": data.get("usage", {}),
        }

    async def _stream_openai(self, prompt, model, system_prompt, temperature, max_tokens):
        async with httpx.AsyncClient(timeout=60) as client:
            async with client.stream(
                "POST",
                "https://api.openai.com/v1/chat/completions",
                headers={"Authorization": f"Bearer {self.api_key}"},
                json={
                    "model": model,
                    "messages": self._messages(prompt, system_prompt),
                    "temperature": temperature,
                    "max_tokens": max_tokens,
                    "stream": True,
                },
            ) as resp:
                resp.raise_for_status()
                async for line in resp.aiter_lines():
                    if not line.startswith("data:"):
                        continue
                    payload = line[5:].strip()
                    if payload == "[DONE]":
                        break
                    try:
                        delta = json.loads(payload)["choices"][0]["delta"].get("content")
                    except (KeyError, IndexError, json.JSONDecodeError):
                        continue
                    if delta:
                        yield delta

    # --- Anthropic ---
    async def _complete_anthropic(self, prompt, model, system_prompt, temperature, max_tokens):
        async with httpx.AsyncClient(timeout=60) as client:
            body = {
                "model": model,
                "max_tokens": max_tokens,
                "temperature": temperature,
                "messages": [{"role": "user", "content": prompt}],
            }
            if system_prompt:
                body["system"] = system_prompt
            resp = await client.post(
                "https://api.anthropic.com/v1/messages",
                headers={
                    "x-api-key": self.api_key,
                    "anthropic-version": "2023-06-01",
                    "content-type": "application/json",
                },
                json=body,
            )
            resp.raise_for_status()
            data = resp.json()
        text = "".join(block.get("text", "") for block in data.get("content", []))
        return text, {"model": data.get("model"), "usage": data.get("usage", {})}

    async def _stream_anthropic(self, prompt, model, system_prompt, temperature, max_tokens):
        body = {
            "model": model,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "stream": True,
            "messages": [{"role": "user", "content": prompt}],
        }
        if system_prompt:
            body["system"] = system_prompt
        async with httpx.AsyncClient(timeout=60) as client:
            async with client.stream(
                "POST",
                "https://api.anthropic.com/v1/messages",
                headers={
                    "x-api-key": self.api_key,
                    "anthropic-version": "2023-06-01",
                    "content-type": "application/json",
                },
                json=body,
            ) as resp:
                resp.raise_for_status()
                async for line in resp.aiter_lines():
                    if not line.startswith("data:"):
                        continue
                    try:
                        event = json.loads(line[5:].strip())
                    except json.JSONDecodeError:
                        continue
                    if event.get("type") == "content_block_delta":
                        delta = event.get("delta", {}).get("text", "")
                        if delta:
                            yield delta

    # --- Gemini ---
    async def _complete_gemini(self, prompt, model, system_prompt, temperature, max_tokens):
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={self.api_key}"
        contents = []
        if system_prompt:
            contents.append({"parts": [{"text": system_prompt}], "role": "user"})
        contents.append({"parts": [{"text": prompt}]})
        async with httpx.AsyncClient(timeout=60) as client:
            resp = await client.post(
                url,
                json={
                    "contents": contents,
                    "generationConfig": {"temperature": temperature, "maxOutputTokens": max_tokens},
                },
            )
            resp.raise_for_status()
            data = resp.json()
        candidates = data.get("candidates", [])
        text = candidates[0]["content"]["parts"][0]["text"] if candidates else ""
        return text, {"model": model, "usage": {}}

    async def _stream_gemini(self, prompt, model, system_prompt, temperature, max_tokens):
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:streamGenerateContent?alt=sse&key={self.api_key}"
        contents = []
        if system_prompt:
            contents.append({"parts": [{"text": system_prompt}], "role": "user"})
        contents.append({"parts": [{"text": prompt}]})
        async with httpx.AsyncClient(timeout=60) as client:
            async with client.stream(
                "POST",
                url,
                json={
                    "contents": contents,
                    "generationConfig": {"temperature": temperature, "maxOutputTokens": max_tokens},
                },
            ) as resp:
                resp.raise_for_status()
                async for line in resp.aiter_lines():
                    if not line.startswith("data:"):
                        continue
                    try:
                        data = json.loads(line[5:].strip())
                    except json.JSONDecodeError:
                        continue
                    for candidate in data.get("candidates", []):
                        for part in candidate.get("content", {}).get("parts", []):
                            if part.get("text"):
                                yield part["text"]

    @staticmethod
    def _messages(prompt: str, system_prompt: str) -> list[dict[str, str]]:
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        return messages

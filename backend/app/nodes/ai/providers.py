from typing import Any, Dict, List, Optional

import httpx


class LLMProviderError(Exception):
    pass


class BaseLLMProvider:
    """Interface implemented by every LLM provider.

    ``complete`` returns a dict with at least ``{"content": str}`` plus any
    provider-specific metadata.
    """

    name: str = "base"

    async def complete(
        self,
        *,
        model: str,
        messages: List[Dict[str, str]],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        json_mode: bool = False,
        timeout: float = 60.0,
    ) -> Dict[str, Any]:
        raise NotImplementedError


class OpenAICompatProvider(BaseLLMProvider):
    """Works with any OpenAI-compatible /chat/completions endpoint.
    Covers OpenAI, Groq, and Ollama (which emulate the OpenAI protocol)."""

    name = "openai_compat"

    def __init__(self, base_url: str, api_key: str = ""):
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key

    async def complete(self, *, model, messages, temperature, max_tokens, json_mode, timeout=60.0):
        payload: Dict[str, Any] = {"model": model, "messages": messages}
        if temperature is not None:
            payload["temperature"] = temperature
        if max_tokens is not None:
            payload["max_tokens"] = max_tokens
        if json_mode:
            payload["response_format"] = {"type": "json_object"}

        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"

        try:
            async with httpx.AsyncClient(timeout=timeout) as client:
                resp = await client.post(
                    f"{self.base_url}/chat/completions", json=payload, headers=headers
                )
        except httpx.TimeoutException:
            raise LLMProviderError(f"{self.name}: request timed out after {timeout}s.")
        except httpx.HTTPError as e:
            raise LLMProviderError(f"{self.name}: request error: {e}")

        if resp.status_code != 200:
            raise LLMProviderError(
                f"{self.name}: HTTP {resp.status_code}: {resp.text[:300]}"
            )
        data = resp.json()
        try:
            content = data["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError):
            raise LLMProviderError(f"{self.name}: unexpected response shape.")
        return {"content": content or "", "raw": data}


class OllamaProvider(OpenAICompatProvider):
    name = "ollama"

    def __init__(self, base_url: str = "http://localhost:11434", api_key: str = ""):
        super().__init__(base_url.rstrip("/"), api_key)


class AnthropicProvider(BaseLLMProvider):
    name = "anthropic"

    def __init__(self, api_key: str, base_url: str = "https://api.anthropic.com"):
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")

    async def complete(self, *, model, messages, temperature, max_tokens, json_mode, timeout=60.0):
        system = ""
        anthropic_messages = []
        for m in messages:
            if m.get("role") == "system":
                system = m.get("content", "")
            else:
                anthropic_messages.append({"role": m["role"], "content": m.get("content", "")})

        payload: Dict[str, Any] = {
            "model": model,
            "messages": anthropic_messages,
            "max_tokens": max_tokens or 1024,
        }
        if system:
            payload["system"] = system
        if temperature is not None:
            payload["temperature"] = temperature

        headers = {
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01",
            "Content-Type": "application/json",
        }
        try:
            async with httpx.AsyncClient(timeout=timeout) as client:
                resp = await client.post(f"{self.base_url}/v1/messages", json=payload, headers=headers)
        except httpx.TimeoutException:
            raise LLMProviderError("anthropic: request timed out.")
        except httpx.HTTPError as e:
            raise LLMProviderError(f"anthropic: request error: {e}")
        if resp.status_code != 200:
            raise LLMProviderError(f"anthropic: HTTP {resp.status_code}: {resp.text[:300]}")
        data = resp.json()
        try:
            content = "".join(
                b.get("text", "") for b in data.get("content", []) if b.get("type") == "text"
            )
        except Exception:
            raise LLMProviderError("anthropic: unexpected response shape.")
        return {"content": content or "", "raw": data}


PROVIDERS = {
    "openai": lambda cfg: OpenAICompatProvider(
        cfg.get("base_url") or "https://api.openai.com/v1", cfg.get("api_key", "")
    ),
    "groq": lambda cfg: OpenAICompatProvider(
        cfg.get("base_url") or "https://api.groq.com/openai/v1", cfg.get("api_key", "")
    ),
    "ollama": lambda cfg: OllamaProvider(
        cfg.get("base_url") or "http://localhost:11434", cfg.get("api_key", "")
    ),
    "anthropic": lambda cfg: AnthropicProvider(
        cfg.get("api_key", ""),
        cfg.get("base_url") or "https://api.anthropic.com",
    ),
}

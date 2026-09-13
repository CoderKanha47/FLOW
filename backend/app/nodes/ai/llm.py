from typing import Any, Dict

from app.nodes.ai.providers import PROVIDERS, LLMProviderError
from app.nodes.base import BaseNode, NodeSpec, NodeError
from app.nodes.registry import register


@register
class LLMNode(BaseNode):
    spec = NodeSpec(
        type="llm",
        label="LLM",
        category="AI",
        icon="🤖",
        fields=[
            {
                "key": "provider",
                "label": "Provider",
                "type": "select",
                "options": ["openai", "groq", "ollama", "anthropic"],
            },
            {"key": "model", "label": "Model", "type": "text"},
            {
                "key": "api_key",
                "label": "API Key",
                "type": "text",
                "help": 'Plain value or reference like {{variables.openai_api_key}}.',
                "secret": True,
            },
            {"key": "base_url", "label": "Base URL (custom/Ollama)", "type": "text"},
            {"key": "system_prompt", "label": "System Prompt", "type": "textarea"},
            {"key": "user_prompt", "label": "User Prompt", "type": "textarea"},
            {"key": "temperature", "label": "Temperature", "type": "number"},
            {"key": "max_tokens", "label": "Max Tokens", "type": "number"},
            {
                "key": "json_mode",
                "label": "Structured (JSON) Output",
                "type": "boolean",
                "default": False,
            },
        ],
    )

    @staticmethod
    def validate(config: Dict[str, Any]) -> list:
        problems = []
        if not (config.get("model") or "").strip():
            problems.append("model is required.")
        if config.get("provider") not in PROVIDERS:
            problems.append(f"provider must be one of {list(PROVIDERS.keys())}.")
        if not (config.get("user_prompt") or "").strip():
            problems.append("user_prompt is required.")
        return problems

    async def execute(self, context, config: Dict[str, Any]) -> Any:
        provider_name = config.get("provider") or "openai"
        model = str(context.render(config.get("model") or ""))
        api_key = context.render(config.get("api_key") or "")
        base_url = context.render(config.get("base_url") or "")
        system_prompt = context.render(config.get("system_prompt") or "")
        user_prompt = context.render(config.get("user_prompt") or "")
        temperature = config.get("temperature")
        max_tokens = config.get("max_tokens")
        json_mode = bool(config.get("json_mode"))

        if temperature is not None:
            try:
                temperature = float(temperature)
            except (TypeError, ValueError):
                temperature = None
        if max_tokens is not None:
            try:
                max_tokens = int(max_tokens)
            except (TypeError, ValueError):
                max_tokens = None

        provider_factory = PROVIDERS.get(provider_name)
        if provider_factory is None:
            raise NodeError(f"Unknown LLM provider: {provider_name}")

        provider = provider_factory({"api_key": api_key, "base_url": base_url})

        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": user_prompt})

        try:
            result = await provider.complete(
                model=model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                json_mode=json_mode,
            )
        except LLMProviderError as e:
            raise NodeError(f"LLM error: {e}")

        content = result["content"]
        data = None
        if json_mode or content.strip().startswith("{"):
            import json

            try:
                data = json.loads(content)
            except json.JSONDecodeError:
                data = None

        usage = (result.get("raw") or {}).get("usage")
        return {
            "content": content,
            "data": data,
            "provider": provider_name,
            "model": model,
            "usage": usage,
        }

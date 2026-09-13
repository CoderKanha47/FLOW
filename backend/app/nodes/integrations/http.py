from typing import Any, Dict

import httpx

from app.nodes.base import BaseNode, NodeSpec, NodeError
from app.nodes.registry import register

METHODS = ["GET", "POST", "PUT", "PATCH", "DELETE", "HEAD", "OPTIONS"]


@register
class HTTPRequestNode(BaseNode):
    spec = NodeSpec(
        type="http_request",
        label="HTTP Request",
        category="Integration",
        icon="🌐",
        fields=[
            {"key": "method", "label": "Method", "type": "select", "options": METHODS},
            {"key": "url", "label": "URL", "type": "text", "placeholder": "https://api.example.com"},
            {
                "key": "params",
                "label": "Query Params (JSON object)",
                "type": "json",
                "help": 'e.g. {"page": "{{input.page}}"}',
            },
            {
                "key": "headers",
                "label": "Headers (JSON object)",
                "type": "json",
                "help": 'e.g. {"Authorization": "Bearer {{variables.api_key}}"}',
            },
            {"key": "body", "label": "Request Body", "type": "json"},
            {"key": "timeout", "label": "Timeout (seconds)", "type": "number", "default": 30},
        ],
    )

    @staticmethod
    def validate(config: Dict[str, Any]) -> list:
        problems = []
        if not (config.get("url") or "").strip():
            problems.append("URL is required.")
        if (config.get("method") or "GET").upper() not in METHODS:
            problems.append(f"Method must be one of {METHODS}.")
        return problems

    def _json_value(self, context, value):
        if value is None or value == "":
            return None
        rendered = context.render(value)
        if isinstance(rendered, str):
            import json

            try:
                return json.loads(rendered)
            except json.JSONDecodeError:
                return rendered
        return rendered

    async def execute(self, context, config: Dict[str, Any]) -> Any:
        method = (config.get("method") or "GET").upper()
        url = str(context.render(config.get("url") or ""))
        params = self._json_value(context, config.get("params")) or {}
        headers = self._json_value(context, config.get("headers")) or {}
        body = self._json_value(context, config.get("body"))
        try:
            timeout = float(config.get("timeout") or 30)
        except (TypeError, ValueError):
            timeout = 30.0

        if not isinstance(headers, dict):
            raise NodeError("Headers must be a JSON object.")
        if not isinstance(params, dict):
            raise NodeError("Query params must be a JSON object.")

        try:
            async with httpx.AsyncClient(timeout=timeout, follow_redirects=True) as client:
                response = await client.request(
                    method,
                    url,
                    params=params,
                    headers=headers,
                    json=body if not isinstance(body, str) else None,
                    content=body if isinstance(body, str) else None,
                )
        except httpx.TimeoutException:
            raise NodeError(f"HTTP request to {url} timed out after {timeout}s.")
        except httpx.HTTPError as e:
            raise NodeError(f"HTTP request failed: {e}")

        data = None
        content_type = response.headers.get("content-type", "")
        if "json" in content_type:
            try:
                data = response.json()
            except ValueError:
                data = None

        return {
            "status_code": response.status_code,
            "headers": dict(response.headers),
            "body": response.text,
            "data": data,
            "ok": 200 <= response.status_code < 300,
            "error": None if 200 <= response.status_code < 300 else response.text,
        }

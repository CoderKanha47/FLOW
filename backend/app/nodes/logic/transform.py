from typing import Any, Dict

from app.nodes.base import BaseNode, NodeSpec, NodeError
from app.nodes.registry import register


@register
class TransformNode(BaseNode):
    spec = NodeSpec(
        type="transform",
        label="Transform",
        category="Logic",
        icon="🔀",
        fields=[
            {
                "key": "mapping",
                "label": "Mapping (JSON object of templates)",
                "type": "json",
                "help": "e.g. {\"currency\": \"INR\", \"amount\": \"{{input.amount}}\"}",
            },
            {
                "key": "expression",
                "label": "Single Expression (optional)",
                "type": "text",
                "help": "If set, evaluated directly as the output instead of mapping.",
            },
        ],
    )

    @staticmethod
    def _load_json(value):
        import json

        if value is None or value == "":
            return None
        if isinstance(value, str):
            try:
                return json.loads(value)
            except json.JSONDecodeError:
                return value
        return value

    @staticmethod
    def validate(config: Dict[str, Any]) -> list:
        expression = config.get("expression")
        mapping = TransformNode._load_json(config.get("mapping"))
        if not expression and not mapping:
            return ["Provide an expression or a mapping."]
        return []

    async def execute(self, context, config: Dict[str, Any]) -> Any:
        expression = (config.get("expression") or "").strip()
        mapping = TransformNode._load_json(config.get("mapping"))

        if expression:
            try:
                out = context.resolve(expression)
            except Exception as e:
                raise NodeError(f"Transform expression error: {e}")
            return context.render(out)

        if isinstance(mapping, dict):
            rendered = context.render(mapping)
            return rendered
        if isinstance(mapping, (list, str)):
            return context.render(mapping)

        raise NodeError("Transform required an expression or object mapping.")

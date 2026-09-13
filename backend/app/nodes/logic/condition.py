from typing import Any, Dict

from app.nodes.base import BaseNode, NodeSpec, NodeError
from app.nodes.registry import register


@register
class ConditionNode(BaseNode):
    spec = NodeSpec(
        type="condition",
        label="Condition",
        category="Logic",
        icon="🔀",
        fields=[
            {
                "key": "expression",
                "label": "Expression",
                "type": "text",
                "placeholder": "amount > 1000",
                "help": "Boolean expression. References prior data as {{input.x}} / {{nodes.ID.output.x}}.",
            }
        ],
    )

    decides_branch = True

    def branch_key(self, output: Any) -> str:
        return "true" if output else "false"

    @staticmethod
    def validate(config: Dict[str, Any]) -> list:
        if not (config.get("expression") or "").strip():
            return ["Condition requires an expression."]
        return []

    async def execute(self, context, config: Dict[str, Any]) -> Any:
        expression = (config.get("expression") or "").strip()
        try:
            result = context.resolve(expression)
        except Exception as e:
            raise NodeError(f"Condition evaluation error: {e}")
        return bool(result)

from typing import Any, Dict

from app.nodes.base import BaseNode, NodeSpec
from app.nodes.registry import register


@register
class ManualTriggerNode(BaseNode):
    spec = NodeSpec(
        type="manual_trigger",
        label="Manual Trigger",
        category="Trigger",
        fields=[
            {
                "key": "defaults",
                "label": "Default Input (JSON)",
                "type": "json",
                "help": "Optional default trigger input as JSON object.",
            }
        ],
    )

    @staticmethod
    def validate(config: Dict[str, Any]) -> list:
        problems = []
        defaults = config.get("defaults")
        if defaults:
            import json

            if isinstance(defaults, str):
                try:
                    json.loads(defaults)
                except json.JSONDecodeError:
                    problems.append("defaults must be valid JSON.")
            elif not isinstance(defaults, dict):
                problems.append("defaults must be a JSON object.")
        return problems

    async def execute(self, context, config: Dict[str, Any]) -> Any:
        return context.trigger_input

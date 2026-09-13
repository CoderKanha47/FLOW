from typing import Any, Dict

from app.nodes.base import BaseNode, NodeSpec
from app.nodes.registry import register


@register
class ScheduleTriggerNode(BaseNode):
    spec = NodeSpec(
        type="schedule_trigger",
        label="Schedule Trigger",
        category="Trigger",
        fields=[
            {
                "key": "cron",
                "label": "Cron Expression",
                "type": "text",
                "placeholder": "0 * * * *",
                "help": "5-field cron expression. (MVP: validated on execution).",
            }
        ],
    )

    @staticmethod
    def validate(config: Dict[str, Any]) -> list:
        cron = (config.get("cron") or "").strip()
        if not cron:
            return ["cron is required for schedule trigger."]
        parts = cron.split()
        if len(parts) != 5:
            return ["cron must have 5 fields (min hour day month weekday)."]
        return []

    async def execute(self, context, config: Dict[str, Any]) -> Any:
        return context.trigger_input

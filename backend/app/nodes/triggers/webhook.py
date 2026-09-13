from typing import Any, Dict

from app.nodes.base import BaseNode, NodeSpec
from app.nodes.registry import register


@register
class WebhookTriggerNode(BaseNode):
    spec = NodeSpec(
        type="webhook",
        label="Webhook Trigger",
        category="Trigger",
        fields=[],
    )

    async def execute(self, context, config: Dict[str, Any]) -> Any:
        return context.trigger_input

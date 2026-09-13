from typing import Any, Dict

from app.nodes.base import BaseNode, NodeSpec
from app.nodes.registry import register


@register
class LogNode(BaseNode):
    spec = NodeSpec(
        type="log",
        label="Log",
        category="Utility",
        icon="📝",
        fields=[
            {
                "key": "message",
                "label": "Message",
                "type": "text",
                "help": 'e.g. "Got result: {{nodes.http_request.data}}"',
            }
        ],
    )

    async def execute(self, context, config: Dict[str, Any]) -> Any:
        rendered = context.render(config.get("message") or "")
        return {"logged": rendered}

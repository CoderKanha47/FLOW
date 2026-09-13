"""Base node abstraction.

Every node implementation conforms to a common execution contract:
the engine calls ``execute(context, config)`` and receives an output.
The engine never needs to know how each node works internally.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional


class NodeError(Exception):
    """Raised when a node fails to execute. Message is recorded in ExecutionNode."""

    pass


class NodeSpec:
    """Static metadata describing a node type for the UI / registry.

    ``fields`` describes the configuration schema so the frontend can generate
    a configuration panel rather than hard-coding one per node.
    """

    def __init__(
        self,
        type: str,
        label: str,
        category: str,
        description: str = "",
        inputs: int = 1,
        outputs: int = 1,
        icon: str = "⚙️",
        fields: Optional[List[Dict[str, Any]]] = None,
    ):
        self.type = type
        self.label = label
        self.category = category
        self.description = description
        self.inputs = inputs
        self.outputs = outputs
        self.icon = icon
        self.fields = fields or []


class BaseNode(ABC):
    """Common interface implemented by every node."""

    # Subclasses override with their own spec.
    spec: NodeSpec

    # True for branching nodes (Condition/Switch) whose outgoing edges select
    # a branch based on the node output.
    decides_branch = False

    def branch_key(self, output: Any) -> str:
        """Map node output to the branch identifier used in edge 'branch' fields."""
        return str(output)

    async def execute(self, context: Any, config: Dict[str, Any]) -> Any:
        """Execute the node.

        Args:
            context: the ExecutionContext (read-only state access).
            config: the node's configuration.

        Returns:
            The node's output value (any JSON-serializable Python object).
        """
        raise NotImplementedError

    @staticmethod
    def validate(config: Dict[str, Any]) -> List[str]:
        """Return a list of configuration problems (strings). Empty when valid."""
        return []

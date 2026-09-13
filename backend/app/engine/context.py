"""Execution context passed to every node.

Nodes read state from this context (the docs' `ExecutionContext`). The context
holds trigger input, outputs of previously executed nodes, and workflow
variables, and exposes helpers for template interpolation and expression
resolution so individual nodes never scatter their own string-parsing logic.
"""

from typing import Any, Dict, Optional

from app.engine import expressions


class ExecutionContext:
    def __init__(
        self,
        workflow_id: str,
        execution_id: str,
        trigger: str,
        trigger_input: Dict[str, Any],
        variables: Optional[Dict[str, Any]] = None,
    ):
        self.workflow_id = workflow_id
        self.execution_id = execution_id
        self.trigger = trigger
        self.trigger_input = trigger_input or {}
        self.variables = variables or {}

        # node_id -> its stored output
        self.outputs: Dict[str, Any] = {}

        # node_id -> its stored input (for auditability)
        self.node_inputs: Dict[str, Any] = {}

        self._node_names: Dict[str, str] = {}

    def register_node_name(self, node_id: str, name: str = "") -> None:
        self._node_names[node_id] = name

    def set_output(self, node_id: str, output: Any, node_input: Any) -> None:
        self.outputs[node_id] = output
        self.node_inputs[node_id] = node_input

    def namespace(self) -> Dict[str, Any]:
        """Assemble the merged namespace used to resolve ``{{ ... }}`` refs."""
        nodes = {nid: {"output": out} for nid, out in self.outputs.items()}
        return {
            "trigger": self.trigger_input,
            "input": self.trigger_input,
            "nodes": nodes,
            "variables": self.variables,
            **_flatten_variables(self.variables),
        }

    def render(self, value: Any) -> Any:
        """Recursively interpolate ``{{ ... }}`` in strings/dicts/lists."""
        return _render_value(value, self.namespace())

    def resolve(self, expression: str, extra: Optional[Dict[str, Any]] = None) -> Any:
        """Evaluate a standalone expression against the merged namespace."""
        context = self.namespace()
        if extra:
            context = {**context, **extra}
        return expressions.evaluate(expression, context)


def _render_value(value: Any, ns: Dict[str, Any]) -> Any:
    if isinstance(value, str):
        return expressions.interpolate(value, ns)
    if isinstance(value, dict):
        return {k: _render_value(v, ns) for k, v in value.items()}
    if isinstance(value, list):
        return [_render_value(v, ns) for v in value]
    return value


def _flatten_variables(variables: Dict[str, Any]) -> Dict[str, Any]:
    """Expose top-level variable names directly as names too, so
    ``{{ my_var }}`` works as well as ``{{ variables.my_var }}``."""
    return {k: v for k, v in variables.items()}

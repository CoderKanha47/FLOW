"""The execution engine.

Runs a validated Graph against trigger input, producing a per-node execution
record. This module is pure logic — it does NOT touch the database, so it can
be tested independently of the UI and persistence (see tests/).
"""

import time
from typing import Any, Dict, List, Optional

from app.engine.context import ExecutionContext
from app.engine.graph import Graph, GraphValidationError
from app.nodes.base import NodeError
from app.nodes.registry import NODE_REGISTRY


class NodeRun:
    def __init__(self, node_id: str, node_type: str, name: str = ""):
        self.node_id = node_id
        self.node_type = node_type
        self.name = name
        self.status = "running"
        self.input: Any = None
        self.output: Any = None
        self.error: Optional[str] = None
        self.duration_ms: Optional[int] = None
        self.started_at: float = 0.0

    def as_dict(self) -> Dict[str, Any]:
        return {
            "node_id": self.node_id,
            "node_type": self.node_type,
            "name": self.name,
            "status": self.status,
            "input": self.input,
            "output": self.output,
            "error": self.error,
            "duration_ms": self.duration_ms,
        }


class ExecutionResult:
    def __init__(self):
        self.status = "running"
        self.output: Any = None
        self.error: Optional[str] = None
        self.nodes: List[NodeRun] = []
        self.duration_ms: int = 0

    def as_dict(self) -> Dict[str, Any]:
        return {
            "status": self.status,
            "output": self.output,
            "error": self.error,
            "duration_ms": self.duration_ms,
            "nodes": [n.as_dict() for n in self.nodes],
        }


async def run_workflow(
    graph: Graph,
    trigger_input: Dict[str, Any],
    trigger: str = "manual",
    variables: Optional[Dict[str, Any]] = None,
    workflow_id: str = "",
    execution_id: str = "",
) -> ExecutionResult:
    result = ExecutionResult()
    started = time.monotonic()

    # Detect cycles (MVP does not yet support loops).
    trigger_node = graph.trigger_node
    if graph.has_cycle_from(trigger_node.id):
        result.status = "failed"
        result.error = "Workflow contains a cycle; loops are not supported yet."
        result.duration_ms = _ms(started)
        return result

    context = ExecutionContext(
        workflow_id=workflow_id,
        execution_id=execution_id,
        trigger=trigger,
        trigger_input=trigger_input,
        variables=variables,
    )

    executed: Dict[str, NodeRun] = {}
    order: List[str] = []
    decisions: Dict[str, str] = {}

    def is_active_incoming(node_id: str) -> bool:
        edges = graph.incoming(node_id)
        active = []
        for e in edges:
            src = e["source"]
            branch = e.get("branch")
            src_is_branching = getattr(
                NODE_REGISTRY.get(graph.nodes[src].type, None), "decides_branch", False
            )
            if not branch or not src_is_branching:
                # Plain edge, or a branch label on a non-branching node: always active.
                active.append(src)
                continue
            # Branch edge: only active when the source decided that branch.
            if src in decisions and decisions[src] == branch:
                active.append(src)
        return active

    def is_ready(node_id: str) -> bool:
        if node_id in executed:
            return False
        if node_id == trigger_node.id:
            return True
        active = is_active_incoming(node_id)
        if not active:
            return False
        # MVP merge semantics: a node runs when at least one active predecessor
        # has completed. (Branches that are never taken do not block the flow.)
        return any(src in executed for src in active)

    # Execute until no more ready nodes.
    progress = True
    while progress:
        progress = False
        ready = [nid for nid in graph.nodes if is_ready(nid)]
        for nid in ready:
            node = graph.nodes[nid]
            impl_cls = NODE_REGISTRY[node.type]

            run = NodeRun(nid, node.type, node.name)
            context.register_node_name(nid, node.name)
            run.started_at = time.monotonic()
            inst = impl_cls()

            # Build the node input (prior outputs snapshot) for auditability.
            run.input = context.namespace()

            try:
                node_config = context.render(graph.nodes[nid].config)
                output = await inst.execute(context, node_config)
                run.status = "success"
                run.output = output
                context.set_output(nid, output, run.input)
                if getattr(inst, "decides_branch", False):
                    decisions[nid] = str(inst.branch_key(output))
            except NodeError as e:
                run.status = "failed"
                run.error = str(e)
            except Exception as e:  # noqa: BLE001
                run.status = "failed"
                run.error = f"{type(e).__name__}: {e}"

            run.duration_ms = _ms(run.started_at)
            executed[nid] = run
            order.append(nid)
            result.nodes.append(run)
            progress = True

    result.duration_ms = _ms(started)

    if not order:
        result.status = "failed"
        result.error = "No nodes could be executed."
        return result

    failed_runs = [r for r in result.nodes if r.status == "failed"]
    if failed_runs:
        result.status = "failed"
        last_failed = failed_runs[-1]
        result.error = f"Node '{last_failed.node_id}' ({last_failed.node_type}) failed: {last_failed.error}"
        return result

    result.status = "success"
    result.output = executed[order[-1]].output
    return result


def _ms(start: float) -> int:
    return int(round((time.monotonic() - start) * 1000))

"""Graph: the runtime representation of a workflow.

The graph is built from persisted nodes+edges, validated, and used by the
executor to determine starting nodes and the next nodes after each execution.
"""

from typing import Any, Dict, List, Optional, Set

from app.engine import expressions
from app.nodes.registry import NODE_REGISTRY

TRIGGER_TYPES = {
    "manual_trigger",
    "webhook",
    "webhook_trigger",
    "schedule_trigger",
    "websocket_trigger",
}


class NodeData:
    def __init__(self, node_id: str, node_type: str, name: str, config: Dict[str, Any]):
        self.id = node_id
        self.type = node_type
        self.name = name
        self.config = config or {}


class GraphValidationError(Exception):
    def __init__(self, problems: List[str]):
        self.problems = problems
        super().__init__("; ".join(problems))


class Graph:
    def __init__(self, nodes: List[NodeData], edges: List[Dict[str, Any]]):
        self.nodes = {n.id: n for n in nodes}
        self.edges: List[Dict[str, Any]] = list(edges)
        self._validate()

    def _validate(self) -> None:
        problems: List[str] = []

        if not self.nodes:
            problems.append("Workflow has no nodes.")

        for e in self.edges:
            src = e.get("source")
            tgt = e.get("target")
            if src not in self.nodes:
                problems.append(f"Edge references unknown source node '{src}'.")
            if tgt not in self.nodes:
                problems.append(f"Edge references unknown target node '{tgt}'.")
            branch = e.get("branch")
            if branch and src in self.nodes:
                src_impl = NODE_REGISTRY.get(self.nodes[src].type)
                if not (src_impl is not None and getattr(src_impl, "decides_branch", False)):
                    problems.append(
                        f"Edge '{e.get('id') or ''}' from non-branching node '{src}' cannot carry a branch label."
                    )

        for nid, node in self.nodes.items():
            if node.type not in NODE_REGISTRY:
                problems.append(f"Unsupported node type '{node.type}' (node '{nid}').")
            else:
                impl = NODE_REGISTRY[node.type]
                config_problems = impl.validate(node.config)
                for p in config_problems:
                    problems.append(f"Node '{nid}' ({node.type}): {p}")

        triggers = [nid for nid, n in self.nodes.items() if n.type in TRIGGER_TYPES]
        if not triggers:
            problems.append("Workflow has no trigger node (manual_trigger, webhook, schedule_trigger required).")
        elif len(triggers) > 1:
            problems.append(
                f"Workflow has multiple trigger nodes ({', '.join(triggers)}). Exactly one is required."
            )

        if problems:
            raise GraphValidationError(problems)

    @property
    def trigger_node(self) -> Optional[NodeData]:
        for n in self.nodes.values():
            if n.type in TRIGGER_TYPES:
                return n
        return None

    @property
    def trigger_type(self) -> Optional[str]:
        trig = self.trigger_node
        return trig.type if trig else None

    def outgoing(self, node_id: str) -> List[Dict[str, Any]]:
        return [e for e in self.edges if e["source"] == node_id]

    def outgoing_targets(self, node_id: str) -> List[str]:
        return [e["target"] for e in self.outgoing(node_id)]

    def incoming(self, node_id: str) -> List[Dict[str, Any]]:
        return [e for e in self.edges if e["target"] == node_id]

    def resolve_next(self, node_id: str, node_output: Any) -> List[str]:
        """Determine the next node(s) after ``node_id`` produced ``node_output``.

        Branching nodes (condition) return multiple possible branches; we pick
        the edges whose ``branch`` equals the decided branch. For nodes with a
        single output, we follow all outgoing edges (excluding conditional edges).
        """
        edges = self.outgoing(node_id)
        if not edges:
            return []

        # Determine if this node is a branching node.
        impl = NODE_REGISTRY.get(self.nodes[node_id].type)
        decided = None
        if impl is not None and getattr(impl, "decides_branch", False):
            decided = str(impl.branch_key(node_output))

        if decided is not None:
            next_ids = [
                e["target"]
                for e in edges
                if (e.get("branch") or "true") == decided
                or (e.get("branch") in (None, "") and len(edges) == 1)
            ]
            return _dedupe(next_ids)

        # Non-branching node: branch labels are meaningless here; follow all edges.
        next_ids = [e["target"] for e in edges]
        return _dedupe(next_ids)

    def has_cycle_from(self, start: str) -> bool:
        visited: Set[str] = set()
        stack: Set[str] = set()

        def visit(nid: str) -> bool:
            if nid in stack:
                return True
            if nid in visited:
                return False
            visited.add(nid)
            stack.add(nid)
            for nxt in self.outgoing_targets(nid):
                if visit(nxt):
                    return True
            stack.discard(nid)
            return False

        return visit(start)


def _dedupe(items: List[str]) -> List[str]:
    seen: Set[str] = set()
    out = []
    for i in items:
        if i not in seen:
            seen.add(i)
            out.append(i)
    return out

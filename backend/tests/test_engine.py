"""Pure execution-engine tests. No database/UI required.

These exercise the heart of Flow: graph execution, branching, failures, and
validation — the doc's "the engine should be testable independently of the UI".
"""

import asyncio

import pytest

from app.engine.executor import run_workflow
from app.engine.graph import Graph, GraphValidationError, NodeData


def run(graph, payload):
    return asyncio.run(run_workflow(graph, payload))

# Importing nodes registers them.
import app.nodes  # noqa: F401  (registers nodes)
from app.nodes.base import NodeError, NodeSpec
from app.nodes.registry import register


@pytest.fixture(autouse=True)
def _ensure_nodes():
    import app.nodes
    return app.nodes


def make_node(nid, ntype, config=None, name=""):
    return NodeData(node_id=nid, node_type=ntype, name=name, config=config or {})


def build(nodes, edges):
    return Graph(nodes, edges)


def test_linear_chain_execution():
    """A -> B -> C executes every node in order and returns the final output."""
    graph = build(
        [
            make_node("t", "manual_trigger"),
            make_node("tr", "transform", {"expression": '{"msg": input.value + "!"}'}),
            make_node("lo", "log", {"message": "logged {{nodes.tr.output.msg}}"}),
        ],
        [
            {"source": "t", "target": "tr"},
            {"source": "tr", "target": "lo"},
        ],
    )
    result = run(graph, {"value": "hi"})
    assert result.status == "success"
    node_ids = [n.node_id for n in result.nodes]
    assert node_ids == ["t", "tr", "lo"]
    assert result.output["logged"] == "logged hi!"
    tr_run = next(n for n in result.nodes if n.node_id == "tr")
    assert tr_run.output == {"msg": "hi!"}


def test_branching_true_path():
    """A -> Condition -> B (true) / C (false). Only the true branch runs."""
    graph = build(
        [
            make_node("t", "manual_trigger"),
            make_node("tr", "transform", {"expression": '{"amount": input.amount}'}),
            make_node("c", "condition", {"expression": "nodes.tr.output.amount > 1000"}),
            make_node("b", "log", {"message": "high value"}),
            make_node("cc", "log", {"message": "low value"}),
        ],
        [
            {"source": "t", "target": "tr"},
            {"source": "tr", "target": "c"},
            {"source": "c", "target": "b", "branch": "true"},
            {"source": "c", "target": "cc", "branch": "false"},
        ],
    )
    result = run(graph, {"amount": 5000})
    assert result.status == "success"
    ran = [n.node_id for n in result.nodes]
    assert "b" in ran
    assert "cc" not in ran
    assert result.output["logged"] == "high value"


def test_branching_false_path():
    graph = build(
        [
            make_node("t", "manual_trigger"),
            make_node("c", "condition", {"expression": "input.amount > 1000"}),
            make_node("b", "log", {"message": "true-branch"}),
            make_node("cc", "log", {"message": "false-branch"}),
        ],
        [
            {"source": "t", "target": "c"},
            {"source": "c", "target": "b", "branch": "true"},
            {"source": "c", "target": "cc", "branch": "false"},
        ],
    )
    result = run(graph, {"amount": 5})
    assert result.status == "success"
    ran = [n.node_id for n in result.nodes]
    assert "b" not in ran
    assert "cc" in ran
    assert result.output["logged"] == "false-branch"


def test_merge_convergence():
    """Both branches converge into a merge point that runs once after both."""
    graph = build(
        [
            make_node("t", "manual_trigger"),
            make_node("c", "condition", {"expression": "input.amount > 0"}),
            make_node("b", "log", {"message": "A"}),
            make_node("cc", "log", {"message": "B"}),
            make_node("m", "log", {"message": "merged"}),
        ],
        [
            {"source": "t", "target": "c"},
            {"source": "c", "target": "b", "branch": "true"},
            {"source": "c", "target": "cc", "branch": "false"},
            {"source": "b", "target": "m"},
            {"source": "cc", "target": "m"},
        ],
    )
    result = run(graph, {"amount": 1})
    assert result.status == "success"
    assert result.output["logged"] == "merged"


def test_failure_propagates_to_workflow():
    """A failed node marks the workflow failed and records the error."""
    graph = build(
        [
            make_node("t", "manual_trigger"),
            make_node("x", "http_request", {"url": "http://127.0.0.1:1", "method": "GET", "timeout": 0.01}),
            make_node("lo", "log", {"message": "after"}),
        ],
        [
            {"source": "t", "target": "x"},
            {"source": "x", "target": "lo"},
        ],
    )
    result = run(graph, {})
    assert result.status == "failed"
    assert result.error is not None
    assert any(n.status == "failed" for n in result.nodes)


def test_missing_node_type_is_invalid():
    nodes = [make_node("t", "manual_trigger"), make_node("bad", "not_a_real_type")]
    with pytest.raises(GraphValidationError):
        build(nodes, [{"source": "t", "target": "bad"}])


def test_invalid_edge_references_unknown_target():
    nodes = [make_node("t", "manual_trigger")]
    with pytest.raises(GraphValidationError):
        build(nodes, [{"source": "t", "target": "ghost"}])
    with pytest.raises(GraphValidationError):
        build([], [])


def test_branch_label_on_non_branching_edge_does_not_block():
    """Even if an invalid graph with a branch label on a non-branching node
    reaches the executor (e.g. legacy persisted data that predates validation),
    traversal must not gate on that edge — downstream nodes still run. (Regression.)"""
    nodes = [
        make_node("t", "manual_trigger"),
        make_node("tr", "transform", {"expression": "input.amount * 2"}),
        make_node("lo", "log", {"message": "done"}),
    ]
    edges = [
        {"source": "t", "target": "tr", "branch": "true"},
        {"source": "tr", "target": "lo", "branch": "true"},
    ]
    graph = object.__new__(Graph)
    graph.nodes = {n.id: n for n in nodes}
    graph.edges = list(edges)
    result = run(graph, {"amount": 60})
    assert result.status == "success"
    node_ids = [n.node_id for n in result.nodes]
    assert node_ids == ["t", "tr", "lo"]


def test_branch_label_on_non_branching_node_rejected_at_validation():
    nodes = [
        make_node("t", "manual_trigger"),
        make_node("lo", "log", {"message": "x"}),
    ]
    with pytest.raises(GraphValidationError) as exc:
        build(nodes, [{"source": "t", "target": "lo", "branch": "true"}])
    assert any("cannot carry a branch label" in p for p in exc.value.problems)


def test_multiple_triggers_invalid():
    nodes = [
        make_node("a", "manual_trigger"),
        make_node("b", "manual_trigger"),
    ]
    with pytest.raises(GraphValidationError) as exc:
        build(nodes, [])
    assert any("multiple trigger" in p for p in exc.value.problems)


def test_node_config_failure():
    """A node missing required config fails validation before execution."""
    with pytest.raises(GraphValidationError):
        build(
            [
                make_node("t", "manual_trigger"),
                make_node("c", "condition", {}),
            ],
            [{"source": "t", "target": "c"}],
        )


def test_cycle_detection():
    graph = build(
        [
            make_node("t", "manual_trigger"),
            make_node("a", "log", {"message": "a"}),
            make_node("b", "log", {"message": "b"}),
        ],
        [
            {"source": "t", "target": "a"},
            {"source": "a", "target": "b"},
            {"source": "b", "target": "a"},
        ],
    )
    result = run(graph, {})
    assert result.status == "failed"
    assert "cycle" in result.error.lower()


def test_invalid_provider_is_a_node_failure():
    """A bad LLM provider config yields a NodeError, recorded as a node failure."""
    import asyncio

    from app.engine.context import ExecutionContext
    from app.nodes.ai.llm import LLMNode

    node = LLMNode()
    ctx = ExecutionContext(workflow_id="w", execution_id="e", trigger="manual", trigger_input={})
    with pytest.raises(NodeError):
        asyncio.run(
            node.execute(ctx, {"provider": "nope", "model": "x", "user_prompt": "hi"})
        )

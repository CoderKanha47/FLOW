from typing import List

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.ids import gen_id
from app.core.security import decrypt_secret, encrypt_secret
from app.engine.graph import Graph, GraphValidationError, NodeData
from app.models.user import User
from app.models.workflow import Workflow, WorkflowEdge, WorkflowNode
from app.schemas import EdgeIn, NodeIn, WorkflowCreate, WorkflowUpdate


def _not_found(wid: str) -> HTTPException:
    return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Workflow {wid} not found")


def _require_owner(workflow: Workflow, user: User) -> Workflow:
    if workflow.user_id != user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not your workflow")
    return workflow


def build_graph_from_orm(workflow: Workflow) -> Graph:
    nodes = [
        NodeData(
            node_id=n.id,
            node_type=n.type,
            name=n.name,
            config=n.config or {},
        )
        for n in workflow.nodes
    ]
    edges = [{"source": e.source, "target": e.target, "branch": e.branch} for e in workflow.edges]
    return Graph(nodes, edges)


def build_graph_from_schemas(nodes: List[NodeIn], edges: List[EdgeIn]) -> Graph:
    node_data = [
        NodeData(n.id, n.type, n.name, n.config)
        for n in nodes
    ]
    edge_data = [{"source": e.source, "target": e.target, "branch": e.branch} for e in edges]
    return Graph(node_data, edge_data)


def create_workflow(db: Session, user: User, payload: WorkflowCreate) -> Workflow:
    workflow = Workflow(
        id=gen_id("wf"),
        user_id=user.id,
        name=payload.name,
        description=payload.description,
        published=payload.published or False,
        webhook_secret_encrypted=encrypt_secret(payload.webhook_secret) if payload.webhook_secret else None,
    )
    db.add(workflow)
    db.flush()

    _sync_nodes_edges(db, workflow, payload.nodes, payload.edges)
    db.commit()
    db.refresh(workflow)
    return workflow


def get_workflow(db: Session, user: User, workflow_id: str) -> Workflow:
    workflow = db.query(Workflow).filter(Workflow.id == workflow_id).first()
    if not workflow:
        raise _not_found(workflow_id)
    return _require_owner(workflow, user)


def get_workflow_secret(workflow: Workflow) -> str | None:
    if not workflow.webhook_secret_encrypted:
        return None
    return decrypt_secret(workflow.webhook_secret_encrypted)


def list_workflows(db: Session, user: User) -> List[Workflow]:
    return (
        db.query(Workflow)
        .filter(Workflow.user_id == user.id)
        .order_by(Workflow.updated_at.desc())
        .all()
    )


def update_workflow(db: Session, user: User, workflow_id: str, payload: WorkflowUpdate) -> Workflow:
    workflow = get_workflow(db, user, workflow_id)

    if payload.name is not None:
        workflow.name = payload.name
    if payload.description is not None:
        workflow.description = payload.description
    if payload.published is not None:
        workflow.published = payload.published
    if payload.webhook_secret is not None:
        workflow.webhook_secret_encrypted = (
            encrypt_secret(payload.webhook_secret) if payload.webhook_secret else None
        )

    if payload.nodes is not None:
        db.query(WorkflowNode).filter(WorkflowNode.workflow_id == workflow_id).delete()
        db.query(WorkflowEdge).filter(WorkflowEdge.workflow_id == workflow_id).delete()
        db.flush()
        _sync_nodes_edges(db, workflow, payload.nodes, payload.edges)

    db.commit()
    db.refresh(workflow)
    return workflow


def delete_workflow(db: Session, user: User, workflow_id: str) -> None:
    workflow = get_workflow(db, user, workflow_id)
    db.delete(workflow)
    db.commit()


def _sync_nodes_edges(db: Session, workflow: Workflow, nodes: List[NodeIn], edges: List[EdgeIn]) -> None:
    for n in nodes:
        db.add(
            WorkflowNode(
                id=n.id,
                workflow_id=workflow.id,
                type=n.type,
                name=n.name,
                position_x=int(n.position.x),
                position_y=int(n.position.y),
                config=n.config,
            )
        )
    for e in edges:
        db.add(
            WorkflowEdge(
                id=e.id or gen_id("edge"),
                workflow_id=workflow.id,
                source=e.source,
                target=e.target,
                branch=e.branch,
            )
        )

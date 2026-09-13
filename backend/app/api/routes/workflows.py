from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.nodes.registry import all_node_specs
from app.models.user import User
from app.models.workflow import Workflow
from app.schemas import (
    EdgeOut,
    NodeOut,
    NodePosition,
    WorkflowCreate,
    WorkflowOut,
    WorkflowUpdate,
)
from app.services import workflow_service

router = APIRouter(prefix="/api/workflows", tags=["workflows"])


def _serialize(wf: Workflow) -> WorkflowOut:
    return WorkflowOut(
        id=wf.id,
        user_id=wf.user_id,
        name=wf.name,
        description=wf.description or "",
        published=wf.published,
        created_at=wf.created_at,
        updated_at=wf.updated_at,
        nodes=[
            NodeOut(
                id=n.id,
                type=n.type,
                name=n.name or "",
                position=NodePosition(x=n.position_x or 0, y=n.position_y or 0),
                config=n.config or {},
            )
            for n in wf.nodes
        ],
        edges=[
            EdgeOut(id=e.id, source=e.source, target=e.target, branch=e.branch)
            for e in wf.edges
        ],
    )


@router.get("/node-types", response_model=list)
def list_node_types():
    specs = []
    for s in all_node_specs():
        specs.append(
            {
                "type": s.type,
                "label": s.label,
                "category": s.category,
                "description": s.description,
                "icon": s.icon,
                "inputs": s.inputs,
                "outputs": s.outputs,
                "fields": s.fields,
            }
        )
    return specs


@router.post("", response_model=WorkflowOut, status_code=201)
def create_workflow(
    payload: WorkflowCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    try:
        wf = workflow_service.create_workflow(db, user, payload)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))
    return _serialize(wf)


def _get_or_404(db: Session, user: User, workflow_id: str) -> Workflow:
    return workflow_service.get_workflow(db, user, workflow_id)


@router.get("", response_model=list)
def list_workflows(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return [_serialize(w) for w in workflow_service.list_workflows(db, user)]


@router.get("/{workflow_id}", response_model=WorkflowOut)
def get_workflow(
    workflow_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return _serialize(_get_or_404(db, user, workflow_id))


@router.put("/{workflow_id}", response_model=WorkflowOut)
def update_workflow(
    workflow_id: str,
    payload: WorkflowUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    try:
        wf = workflow_service.update_workflow(db, user, workflow_id, payload)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))
    return _serialize(wf)


@router.delete("/{workflow_id}", status_code=204)
def delete_workflow(
    workflow_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    workflow_service.delete_workflow(db, user, workflow_id)

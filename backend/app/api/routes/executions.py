from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.workflow import Execution, ExecutionNode
from app.models.user import User
from app.schemas import RunRequest
from app.services import execution_service, workflow_service

router = APIRouter(prefix="/api", tags=["executions"])


@router.post("/workflows/{workflow_id}/run", status_code=200)
async def run_workflow(
    workflow_id: str,
    payload: RunRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    workflow = workflow_service.get_workflow(db, user, workflow_id)
    execution = await execution_service.execute_workflow(
        db,
        workflow,
        trigger_input=payload.input or {},
        trigger="manual",
        variables=payload.input or {},
        user=user,
    )
    return _serialize_execution(db, execution)


@router.get("/workflows/{workflow_id}/executions", response_model=list)
def workflow_executions(
    workflow_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    workflow_service.get_workflow(db, user, workflow_id)
    executions = execution_service.list_executions(db, user, workflow_id=workflow_id)
    return [_serialize_execution_summary(e) for e in executions]


@router.get("/executions/{execution_id}")
def execution_detail(
    execution_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    execution = execution_service.get_execution(db, user, execution_id)
    return _serialize_execution(db, execution)


def _serialize_execution_summary(e: Execution) -> dict:
    return {
        "id": e.id,
        "workflow_id": e.workflow_id,
        "status": e.status,
        "trigger": e.trigger,
        "started_at": e.started_at.isoformat() if e.started_at else None,
        "ended_at": e.ended_at.isoformat() if e.ended_at else None,
        "duration_ms": e.duration_ms,
        "error": e.error,
    }


def _serialize_execution(db: Session, e: Execution) -> dict:
    nodes = db.query(ExecutionNode).filter(ExecutionNode.execution_id == e.id).all()
    return {
        "id": e.id,
        "workflow_id": e.workflow_id,
        "status": e.status,
        "trigger": e.trigger,
        "trigger_input": e.trigger_input,
        "output": e.output,
        "error": e.error,
        "started_at": e.started_at.isoformat() if e.started_at else None,
        "ended_at": e.ended_at.isoformat() if e.ended_at else None,
        "duration_ms": e.duration_ms,
        "nodes": [
            {
                "id": n.id,
                "node_id": n.node_id,
                "node_type": n.node_type,
                "status": n.status,
                "input": n.input,
                "output": n.output,
                "error": n.error,
                "duration_ms": n.duration_ms,
            }
            for n in nodes
        ],
    }

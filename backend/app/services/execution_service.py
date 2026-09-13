from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.ids import gen_id
from app.engine.executor import run_workflow
from app.engine.graph import GraphValidationError
from app.models.workflow import Execution, ExecutionNode
from app.models.user import User
from app.models.workflow import Workflow
from app.services import workflow_service


def _now() -> datetime:
    return datetime.now(timezone.utc)


async def execute_workflow(
    db: Session,
    workflow: Workflow,
    trigger_input: dict,
    trigger: str = "manual",
    variables: dict | None = None,
    user: User | None = None,
) -> Execution:
    """Build the graph, run it, and persist the execution + node history."""
    execution_id = gen_id("ex")
    execution = Execution(
        id=execution_id,
        workflow_id=workflow.id,
        user_id=workflow.user_id,
        status="running",
        trigger=trigger,
        trigger_input=trigger_input or {},
        started_at=_now(),
    )
    db.add(execution)
    db.flush()

    try:
        graph = workflow_service.build_graph_from_orm(workflow)
        result = await run_workflow(
            graph,
            trigger_input or {},
            trigger=trigger,
            variables=variables,
            workflow_id=workflow.id,
            execution_id=execution_id,
        )
    except GraphValidationError as e:
        execution.status = "failed"
        execution.error = "; ".join(e.problems)
        execution.ended_at = _now()
        db.commit()
        db.refresh(execution)
        return execution

    for nr in result.nodes:
        db.add(
            ExecutionNode(
                id=gen_id("exn"),
                execution_id=execution_id,
                node_id=nr.node_id,
                node_type=nr.node_type,
                status=nr.status,
                input=nr.input,
                output=nr.output,
                error=nr.error,
                duration_ms=nr.duration_ms,
                started_at=_now(),
                completed_at=_now(),
            )
        )

    execution.status = result.status
    execution.output = result.output
    execution.error = result.error
    execution.duration_ms = result.duration_ms
    execution.ended_at = _now()

    db.commit()
    db.refresh(execution)
    return execution


def get_execution(db: Session, user: User, execution_id: str) -> Execution:
    execution = db.query(Execution).filter(Execution.id == execution_id).first()
    if not execution:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Execution not found")
    if execution.user_id != user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not your execution")
    return execution


def list_executions(db: Session, user: User, workflow_id: str | None = None):
    q = db.query(Execution).filter(Execution.user_id == user.id)
    if workflow_id:
        q = q.filter(Execution.workflow_id == workflow_id)
    return q.order_by(Execution.started_at.desc()).limit(50).all()

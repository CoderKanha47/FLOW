import json
import logging

from fastapi import APIRouter, Depends, Header, Request, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.workflow import Workflow
from app.services import execution_service, workflow_service

logger = logging.getLogger("flow.webhooks")
if not logger.handlers:
    _handler = logging.StreamHandler()
    _handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s"))
    logger.addHandler(_handler)
logger.setLevel(logging.INFO)

router = APIRouter(prefix="/api/webhooks", tags=["webhooks"])


def _log_payload(payload: dict) -> str:
    try:
        return json.dumps(payload, default=str)[:2000]
    except Exception:  # noqa: BLE001
        return repr(payload)[:2000]


@router.post("/{workflow_id}")
async def handle_webhook(
    workflow_id: str,
    request: Request,
    db: Session = Depends(get_db),
    x_webhook_secret: str | None = Header(None, alias="X-Webhook-Secret"),
):
    workflow = db.query(Workflow).filter(Workflow.id == workflow_id).first()
    if not workflow:
        logger.warning("Webhook rejected: workflow_id=%s not found", workflow_id)
        return JSONResponse(status_code=status.HTTP_404_NOT_FOUND, content={"error": "Workflow not found"})
    if not workflow.published:
        logger.warning("Webhook rejected: workflow_id=%s is not published", workflow_id)
        return JSONResponse(
            status_code=status.HTTP_403_FORBIDDEN,
            content={"error": "Workflow is not published"},
        )

    secret = workflow_service.get_workflow_secret(workflow)
    if secret and not _safe_equal(x_webhook_secret or "", secret):
        logger.warning("Webhook rejected: workflow_id=%s bad secret", workflow_id)
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={"error": "Invalid webhook secret"},
        )

    body = {}
    content_type = request.headers.get("content-type", "")
    if "json" in content_type:
        try:
            body = await request.json()
        except Exception:  # noqa: BLE001
            body = {}
    else:
        raw = (await request.body()).decode("utf-8", errors="ignore")
        if raw:
            body = {"body": raw}

    if not isinstance(body, dict):
        body = {"data": body}

    logger.info("Webhook received: workflow_id=%s payload=%s", workflow_id, _log_payload(body))

    try:
        execution = await execution_service.execute_workflow(
            db,
            workflow,
            trigger_input=body,
            trigger="webhook",
            variables=body,
        )
    except Exception:  # noqa: BLE001
        logger.exception(
            "Webhook execution raised unexpected exception: workflow_id=%s payload=%s",
            workflow_id,
            _log_payload(body),
        )
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"error": "Workflow execution failed"},
        )

    if execution.status != "success":
        logger.error(
            "Webhook execution failed: workflow_id=%s execution_id=%s status=%s error=%s",
            workflow_id,
            execution.id,
            execution.status,
            execution.error,
        )
        for node in execution.nodes:
            if node.status == "failed":
                logger.error(
                    "Failed node: workflow_id=%s execution_id=%s node_id=%s node_type=%s error=%s",
                    workflow_id,
                    execution.id,
                    node.node_id,
                    node.node_type,
                    node.error,
                )
            else:
                logger.info(
                    "Node ok: execution_id=%s node_id=%s node_type=%s status=%s",
                    execution.id,
                    node.node_id,
                    node.node_type,
                    node.status,
                )
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"error": "Workflow execution failed"},
        )

    logger.info(
        "Webhook execution success: workflow_id=%s execution_id=%s duration_ms=%s",
        workflow_id,
        execution.id,
        execution.duration_ms,
    )
    return JSONResponse(status_code=status.HTTP_200_OK, content=execution.output)


def _safe_equal(a: str, b: str) -> bool:
    import hmac

    return hmac.compare_digest(a, b)
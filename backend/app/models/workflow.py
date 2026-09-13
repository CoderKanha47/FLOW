from datetime import datetime

from sqlalchemy import JSON, Boolean, Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from app.core.database import Base
from app.models.user import utcnow


class Workflow(Base):
    __tablename__ = "workflows"

    id = Column(String, primary_key=True)
    user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String, nullable=False)
    description = Column(Text, default="")
    published = Column(Boolean, default=False)
    webhook_secret_encrypted = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=utcnow)
    updated_at = Column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

    owner = relationship("User", back_populates="workflows")
    nodes = relationship(
        "WorkflowNode", back_populates="workflow", cascade="all, delete-orphan", lazy="selectin"
    )
    edges = relationship(
        "WorkflowEdge", back_populates="workflow", cascade="all, delete-orphan", lazy="selectin"
    )
    executions = relationship("Execution", back_populates="workflow", cascade="all, delete-orphan")


class WorkflowNode(Base):
    __tablename__ = "workflow_nodes"

    id = Column(String, primary_key=True)  # node_id (unique within a workflow)
    # Composite primary key: node ids are scoped to their workflow.
    workflow_id = Column(
        String, ForeignKey("workflows.id", ondelete="CASCADE"), nullable=False, index=True, primary_key=True
    )
    type = Column(String, nullable=False)
    name = Column(String, default="")
    position_x = Column(Integer, default=0)
    position_y = Column(Integer, default=0)
    config = Column(JSON, default=dict)

    workflow = relationship("Workflow", back_populates="nodes")


class WorkflowEdge(Base):
    __tablename__ = "workflow_edges"

    id = Column(String, primary_key=True)  # edge_id (unique within a workflow)
    workflow_id = Column(
        String, ForeignKey("workflows.id", ondelete="CASCADE"), nullable=False, index=True, primary_key=True
    )
    source = Column(String, nullable=False)
    target = Column(String, nullable=False)
    branch = Column(String, nullable=True)  # e.g. "true"/"false"/"default" for conditional

    workflow = relationship("Workflow", back_populates="edges")


class Execution(Base):
    __tablename__ = "executions"

    id = Column(String, primary_key=True)
    workflow_id = Column(String, ForeignKey("workflows.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    status = Column(String, default="running")  # running|success|failed
    trigger = Column(String, default="manual")  # manual|webhook|schedule
    trigger_input = Column(JSON, default=dict)
    output = Column(JSON, nullable=True)
    error = Column(Text, nullable=True)
    started_at = Column(DateTime(timezone=True), default=utcnow)
    ended_at = Column(DateTime(timezone=True), nullable=True)
    duration_ms = Column(Integer, nullable=True)

    workflow = relationship("Workflow", back_populates="executions")
    nodes = relationship("ExecutionNode", back_populates="execution", cascade="all, delete-orphan")


class ExecutionNode(Base):
    __tablename__ = "execution_nodes"

    id = Column(String, primary_key=True)
    execution_id = Column(String, ForeignKey("executions.id", ondelete="CASCADE"), nullable=False, index=True)
    node_id = Column(String, nullable=False)
    node_type = Column(String, nullable=False)
    status = Column(String, default="running")  # running|success|failed|skipped
    input = Column(JSON, nullable=True)
    output = Column(JSON, nullable=True)
    error = Column(Text, nullable=True)
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    duration_ms = Column(Integer, nullable=True)

    execution = relationship("Execution", back_populates="nodes")

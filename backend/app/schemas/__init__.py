from typing import Any, Dict, List, Optional

from pydantic import BaseModel, EmailStr, Field

# --- Auth ---


class UserRegister(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8)


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserOut(BaseModel):
    id: str
    email: EmailStr

    class Config:
        from_attributes = True


# --- Workflow ---


class NodePosition(BaseModel):
    x: float = 0
    y: float = 0


class NodeIn(BaseModel):
    id: str
    type: str
    name: str = ""
    position: NodePosition = NodePosition()
    config: Dict[str, Any] = Field(default_factory=dict)


class EdgeIn(BaseModel):
    id: str
    source: str
    target: str
    branch: Optional[str] = None


class WorkflowCreate(BaseModel):
    name: str
    description: str = ""
    published: Optional[bool] = False
    webhook_secret: Optional[str] = None
    nodes: List[NodeIn] = Field(default_factory=list)
    edges: List[EdgeIn] = Field(default_factory=list)


class WorkflowUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    published: Optional[bool] = None
    webhook_secret: Optional[str] = None
    nodes: Optional[List[NodeIn]] = None
    edges: Optional[List[EdgeIn]] = None


class NodeOut(BaseModel):
    id: str
    type: str
    name: str = ""
    position: NodePosition = NodePosition()
    config: Dict[str, Any] = Field(default_factory=dict)

    class Config:
        from_attributes = True
        arbitrary_types_allowed = True


class EdgeOut(BaseModel):
    id: str
    source: str
    target: str
    branch: Optional[str] = None

    class Config:
        from_attributes = True


class WorkflowOut(BaseModel):
    id: str
    user_id: str
    name: str
    description: str = ""
    published: bool = False
    created_at: Any = None
    updated_at: Any = None
    nodes: List[NodeOut] = Field(default_factory=list)
    edges: List[EdgeOut] = Field(default_factory=list)

    class Config:
        from_attributes = True
        arbitrary_types_allowed = True


class ExecutionOut(BaseModel):
    id: str
    workflow_id: str
    user_id: str
    status: str
    trigger: str = "manual"
    output: Optional[Any] = None
    error: Optional[str] = None
    started_at: Any = None
    ended_at: Any = None
    duration_ms: Optional[int] = None

    class Config:
        from_attributes = True
        arbitrary_types_allowed = True


class ExecutionNodeOut(BaseModel):
    id: str
    execution_id: str
    node_id: str
    node_type: str
    status: str
    input: Optional[Any] = None
    output: Optional[Any] = None
    error: Optional[str] = None
    started_at: Any = None
    completed_at: Any = None
    duration_ms: Optional[int] = None

    class Config:
        from_attributes = True
        arbitrary_types_allowed = True


class RunRequest(BaseModel):
    input: Dict[str, Any] = Field(default_factory=dict)

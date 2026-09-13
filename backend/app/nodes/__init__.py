"""Importing this package registers all built-in nodes."""

from app.nodes.triggers import manual  # noqa: F401
from app.nodes.triggers import schedule  # noqa: F401
from app.nodes.triggers import webhook  # noqa: F401
from app.nodes.logic import transform  # noqa: F401
from app.nodes.logic import condition  # noqa: F401
from app.nodes.integrations import http  # noqa: F401
from app.nodes.integrations import database  # noqa: F401
from app.nodes.ai import llm  # noqa: F401
from app.nodes.utilities import log  # noqa: F401

from app.nodes.base import BaseNode, NodeError, NodeSpec  # noqa: F401

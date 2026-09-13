"""Node registry.

Resolves ``node.type`` -> node implementation.

The executor only ever talks to the registry; adding a new node type means
implementing a ``BaseNode`` subclass and registering it here — the engine
never changes.
"""

from typing import Dict, Type

from app.nodes.base import BaseNode

NODE_REGISTRY: Dict[str, Type[BaseNode]] = {}


def register(node_cls: Type[BaseNode]) -> Type[BaseNode]:
    NODE_REGISTRY[node_cls.spec.type] = node_cls
    return node_cls


def get_node_class(node_type: str):
    return NODE_REGISTRY.get(node_type)


def all_node_specs() -> list:
    return [cls.spec for cls in NODE_REGISTRY.values()]

"""Safe expression/interpolation language for Flow.

Two related features:

1. Template interpolation: replace ``{{ path.to.value }}`` inside strings with
   resolved values from the workflow context.

2. Expression evaluation: for Condition/Switch/Transform, evaluate a boolean or
   transform expression referencing context values.

Security: evaluation is done by walking Python's ``ast`` for a small whitelisted
subset. No arbitrary attribute access, no function calls, no imports, no
subscripting beyond our own resolver. A name is resolved by splitting on ``.``
in our own safe namespace walker (never Python-level attribute access).
"""

import ast
import re
from typing import Any

TEMPLATE_RE = re.compile(r"\{\{\s*(.*?)\s*\}\}")

# Operators we allow inside expressions, mapped to python-safe lowering.
_BINOP = {
    ast.Add: lambda a, b: a + b,
    ast.Sub: lambda a, b: a - b,
    ast.Mult: lambda a, b: a * b,
    ast.Div: lambda a, b: a / b,
    ast.Mod: lambda a, b: a % b,
}

_CMPOP = {
    ast.Gt: lambda a, b: a > b,
    ast.Lt: lambda a, b: a < b,
    ast.GtE: lambda a, b: a >= b,
    ast.LtE: lambda a, b: a <= b,
    ast.Eq: lambda a, b: a == b,
    ast.NotEq: lambda a, b: a != b,
    ast.In: lambda a, b: a in b,
    ast.NotIn: lambda a, b: a not in b,
    ast.Is: lambda a, b: a is b,
    ast.IsNot: lambda a, b: a is not b,
}

_BOOLOP = {
    ast.And: lambda a, b: a and b,
    ast.Or: lambda a, b: a or b,
}


class ExpressionError(Exception):
    pass


class _Resolver:
    """Resolves dotted paths against a namespace dict, then falls back to
    treating the whole expression as an attribute-chain lookup."""

    def __init__(self, namespace: dict):
        self.namespace = namespace

    def resolve(self, name: str) -> Any:
        parts = name.split(".")
        node: Any = self.namespace
        for part in parts:
            if isinstance(node, dict):
                if part not in node:
                    raise ExpressionError(f"Undefined reference: {name}")
                node = node[part]
            elif isinstance(node, list):
                try:
                    node = node[int(part)]
                except (ValueError, IndexError):
                    raise ExpressionError(f"Invalid list index in reference: {name}")
            elif isinstance(node, (list, tuple)):
                raise ExpressionError(f"Cannot index {type(node).__name__} with: {name}")
            else:
                # For simple values with no nesting, leaf is the value itself.
                raise ExpressionError(f"Undefined reference: {name}")
        return node


def _eval_expr(node: ast.AST, resolver: _Resolver) -> Any:
    if isinstance(node, ast.Constant):
        return node.value
    if isinstance(node, ast.Num):  # py<3.8
        return node.n
    if isinstance(node, ast.Str):  # py<3.8
        return node.s
    if isinstance(node, ast.Name):
        return resolver.resolve(node.id)
    if isinstance(node, ast.Attribute):
        # Only used as part of a Name dotted chain; if we get here, resolve the full path.
        raise ExpressionError("Unsupported attribute access in expression")
    if isinstance(node, ast.BinOp):
        op = _BINOP.get(type(node.op))
        if op is None:
            raise ExpressionError("Unsupported binary operator")
        left = _eval_expr(node.left, resolver)
        right = _eval_expr(node.right, resolver)
        try:
            return op(left, right)
        except (TypeError, ZeroDivisionError) as e:
            raise ExpressionError(f"Expression error: {e}")
    if isinstance(node, ast.Compare):
        left = _eval_expr(node.left, resolver)
        for op, comparator in zip(node.ops, node.comparators):
            op_fn = _CMPOP.get(type(op))
            if op_fn is None:
                raise ExpressionError("Unsupported comparison operator")
            right = _eval_expr(comparator, resolver)
            try:
                if not op_fn(left, right):
                    return False
            except TypeError as e:
                raise ExpressionError(f"Comparison error: {e}")
            left = right
        return True
    if isinstance(node, ast.BoolOp):
        values = [_eval_expr(v, resolver) for v in node.values]
        op = _BOOLOP.get(type(node.op))
        if op is None:
            raise ExpressionError("Unsupported boolean operator")
        result = values[0]
        for v in values[1:]:
            result = op(result, v)
        return result
    if isinstance(node, ast.UnaryOp):
        if isinstance(node.op, ast.Not):
            return not _eval_expr(node.operand, resolver)
        if isinstance(node.op, ast.USub):
            return -_eval_expr(node.operand, resolver)
        raise ExpressionError("Unsupported unary operator")
    raise ExpressionError(f"Unsupported expression element: {type(node).__name__}")


def evaluate(expression: str, context: dict) -> Any:
    """Evaluate a standalone boolean/transform expression against ``context``.

    ``context`` should contain all namespaces the expression references
    (normally the merged resolve context).
    """
    expr = expression.strip()
    if not expr:
        return None
    try:
        tree = ast.parse(expr, mode="eval")
    except SyntaxError as e:
        raise ExpressionError(f"Invalid expression: {e.msg}")
    resolver = _Resolver({})
    # Wrap: evaluate with a resolver that yields whole dotted names.
    return _eval(tree, context)


def _eval(node: ast.AST, context: dict) -> Any:
    if isinstance(node, ast.Expression):
        return _eval(node.body, context)
    if isinstance(node, ast.Name):
        return _dotted_get(context, node.id)
    if isinstance(node, ast.Attribute):
        # Build the full dotted name and resolve.
        parts = []
        cur = node
        while isinstance(cur, ast.Attribute):
            parts.append(cur.attr)
            cur = cur.value
        if isinstance(cur, ast.Name):
            parts.append(cur.id)
        path = ".".join(reversed(parts))
        return _dotted_get(context, path)
    if isinstance(node, ast.Constant):
        return node.value
    if isinstance(node, ast.Dict):
        result = {}
        for k, v in zip(node.keys, node.values):
            result[_eval(k, context)] = _eval(v, context)
        return result
    if isinstance(node, ast.List):
        return [_eval(x, context) for x in node.elts]
    if isinstance(node, ast.Tuple):
        return tuple(_eval(x, context) for x in node.elts)
    if isinstance(node, ast.BinOp):
        op = _BINOP.get(type(node.op))
        if op is None:
            raise ExpressionError("Unsupported binary operator")
        return op(_eval(node.left, context), _eval(node.right, context))
    if isinstance(node, ast.Compare):
        left = _eval(node.left, context)
        for op, comparator in zip(node.ops, node.comparators):
            op_fn = _CMPOP.get(type(op))
            if op_fn is None:
                raise ExpressionError("Unsupported comparison operator")
            right = _eval(comparator, context)
            try:
                if not op_fn(left, right):
                    return False
            except TypeError as e:
                raise ExpressionError(f"Comparison error: {e}")
            left = right
        return True
    if isinstance(node, ast.BoolOp):
        op = _BOOLOP.get(type(node.op))
        values = [_eval(v, context) for v in node.values]
        if op is None:
            raise ExpressionError("Unsupported boolean operator")
        result = values[0]
        for v in values[1:]:
            result = op(result, v)
        return result
    if isinstance(node, ast.UnaryOp):
        if isinstance(node.op, ast.Not):
            return not _eval(node.operand, context)
        if isinstance(node.op, ast.USub):
            return -_eval(node.operand, context)
        raise ExpressionError("Unsupported unary operator")
    raise ExpressionError(f"Unsupported expression element: {type(node).__name__}")


def _dotted_get(context: dict, path: str) -> Any:
    parts = path.split(".")
    node: Any = context
    for part in parts:
        if isinstance(node, dict):
            if part not in node:
                raise ExpressionError(f"Undefined reference: {path}")
            node = node[part]
        elif isinstance(node, (list, tuple)):
            try:
                node = node[int(part)]
            except (ValueError, IndexError):
                raise ExpressionError(f"Invalid index in reference: {path}")
        else:
            raise ExpressionError(f"Undefined reference: {path}")
    return node


def interpolate(text: str, context: dict) -> Any:
    """Replace ``{{ refs }}`` in ``text``.

    If the text is exactly one ``{{...}}`` with nothing else, the resolved value
    is returned as-is (preserving types). Otherwise all references are stringified
    into the surrounding text.
    """
    if not isinstance(text, str):
        return text

    matches = list(TEMPLATE_RE.finditer(text))
    if not matches:
        return text

    # Exact single interpolation -> return native value
    if len(matches) == 1 and matches[0].group(0) == text.strip():
        expr = matches[0].group(1).strip()
        return _dotted_get(context, expr) if "." in expr or expr.startswith("trigger") or expr in context else _safe_name(context, expr)

    result = []
    last = 0
    for m in matches:
        result.append(text[last:m.start()])
        expr = m.group(1).strip()
        value = _dotted_get(context, expr) if ("." in expr or expr in context) else _safe_name(context, expr)
        result.append(_stringify(value))
        last = m.end()
    result.append(text[last:])
    return "".join(result)


def _safe_name(context: dict, name: str) -> Any:
    if name in context:
        return context[name]
    return _dotted_get(context, name)


def _stringify(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (dict, list)):
        import json

        return json.dumps(value)
    return str(value)

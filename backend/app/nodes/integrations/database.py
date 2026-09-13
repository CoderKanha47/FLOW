from typing import Any, Dict, List

from sqlalchemy import create_engine, text

from app.nodes.base import BaseNode, NodeSpec, NodeError
from app.nodes.registry import register

OPS = ["select", "insert", "update", "delete"]

# Identifiers are validated to simple [a-zA-Z0-9_]+ to prevent identifier
# injection. Values are always bound parameters. This is the core security
# boundary: no arbitrary SQL from untrusted config.
_IDENT_RE = None


def _valid_ident(name: str) -> bool:
    import re

    return bool(re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", name or ""))


@register
class DatabaseNode(BaseNode):
    spec = NodeSpec(
        type="database",
        label="Database (PostgreSQL)",
        category="Integration",
        icon="🗄️",
        fields=[
            {
                "key": "database_url",
                "label": "Database URL",
                "type": "text",
                "help": 'e.g. postgresql://user:pass@host:5432/db — reference as {{variables.db_url}}.',
            },
            {"key": "operation", "label": "Operation", "type": "select", "options": OPS},
            {"key": "table", "label": "Table", "type": "text"},
            {"key": "columns", "label": "Columns (comma-separated, optional)", "type": "text"},
            {"key": "values", "label": "Values (JSON object for insert/update)", "type": "json"},
            {
                "key": "where",
                "label": "Where (JSON array of {column, operator, value})",
                "type": "json",
                "help": 'e.g. [{"column":"id","operator":"=","value":"{{nodes.http.data.id}}"}]',
            },
            {"key": "limit", "label": "Limit", "type": "number"},
        ],
    )

    @staticmethod
    def validate(config: Dict[str, Any]) -> list:
        problems = []
        if not (config.get("database_url") or "").strip():
            problems.append("database_url is required.")
        if (config.get("operation") or "") not in OPS:
            problems.append(f"operation must be one of {OPS}.")
        table = (config.get("table") or "").strip()
        if not table or not _valid_ident(table):
            problems.append("table must be a simple identifier (letters/digits/underscore).")
        return problems

    def _json(self, value):
        import json

        if value is None or value == "":
            return None
        if isinstance(value, str):
            try:
                return json.loads(value)
            except json.JSONDecodeError:
                return value
        return value

    def _build_where(self, context, where_cfg: list) -> tuple:
        clauses = []
        params = {}
        for i, cond in enumerate(where_cfg or []):
            col = (cond.get("column") or "").strip()
            if not _valid_ident(col):
                raise NodeError(f"Invalid column identifier in where: {col}")
            operator = (cond.get("operator") or "=").strip()
            allowed = ["=", "!=", ">", "<", ">=", "<=", "LIKE", "IN"]
            if operator not in allowed:
                raise NodeError(f"Unsupported operator: {operator}")
            raw_value = context.render(cond.get("value"))
            if operator == "IN" and not isinstance(raw_value, (list, tuple)):
                raise NodeError("IN operator requires a list value.")
            pname = f"p{i}"
            if operator == "IN":
                in_params = ", ".join(f":{pname}_j" for j in range(len(raw_value)))
                clauses.append(f'"{col}" IN ({in_params})')
                for j, v in enumerate(raw_value):
                    params[f"{pname}_j"] = v
            else:
                clauses.append(f'"{col}" {operator} :{pname}')
                params[pname] = raw_value
        return " AND ".join(clauses), params

    def _get_engine(self, config, context):
        url = str(context.render(config.get("database_url") or ""))
        if not url:
            raise NodeError("database_url is required.")
        return create_engine(url, pool_pre_ping=True, poolclass=None)

    async def execute(self, context, config: Dict[str, Any]) -> Any:
        op = config.get("operation")
        table = (config.get("table") or "").strip()

        engine = self._get_engine(config, context)
        try:
            where_sql, where_params = self._build_where(
                context, self._json(config.get("where")) or []
            )

            if op == "select":
                col_cfg = (config.get("columns") or "").strip() or "*"
                cols = [
                    c.strip() for c in col_cfg.split(",") if c.strip()
                ]
                for c in cols:
                    if c != "*" and not _valid_ident(c):
                        raise NodeError(f"Invalid column identifier: {c}")
                col_sql = ", ".join(f'"{c}"' if c != "*" else "*" for c in cols)
                sql = f"SELECT {col_sql} FROM \"{table}\""
                if where_sql:
                    sql += f" WHERE {where_sql}"
                limit = config.get("limit")
                if limit is not None:
                    sql += f" LIMIT {int(limit)}"
                with engine.connect() as conn:
                    rows = conn.execute(text(sql), where_params)
                    columns = list(rows.keys())
                    records = [dict(zip(columns, r)) for r in rows.fetchall()]
                return {"rows": records, "row_count": len(records)}

            if op == "insert":
                values = self._json(config.get("values")) or {}
                if not isinstance(values, dict) or not values:
                    raise NodeError("insert requires a non-empty 'values' JSON object.")
                for c in values:
                    if not _valid_ident(str(c)):
                        raise NodeError(f"Invalid column identifier: {c}")
                rendered = {str(k): context.render(v) for k, v in values.items()}
                cols = ", ".join(f'"{c}"' for c in rendered)
                plist = ", ".join(f":{c}" for c in rendered)
                with engine.begin() as conn:
                    result = conn.execute(
                        text(f'INSERT INTO "{table}" ({cols}) VALUES ({plist}) RETURNING *'),
                        rendered,
                    )
                    columns = list(result.keys())
                    row = result.fetchone()
                return {"rows": [dict(zip(columns, row))] if row else [], "row_count": 1}

            if op == "update":
                values = self._json(config.get("values")) or {}
                if not isinstance(values, dict) or not values:
                    raise NodeError("update requires a non-empty 'values' JSON object.")
                for c in values:
                    if not _valid_ident(str(c)):
                        raise NodeError(f"Invalid column identifier: {c}")
                rendered = {str(k): context.render(v) for k, v in values.items()}
                set_sql = ", ".join(f'"{c}" = :{c}' for c in rendered)
                params = dict(rendered)
                params.update(where_params)
                if where_sql:
                    sql = f'UPDATE "{table}" SET {set_sql} WHERE {where_sql}'
                else:
                    sql = f'UPDATE "{table}" SET {set_sql}'
                with engine.begin() as conn:
                    result = conn.execute(text(sql), params)
                return {"row_count": result.rowcount}

            if op == "delete":
                if not where_sql:
                    raise NodeError("delete requires a 'where' clause (safety).")
                with engine.begin() as conn:
                    result = conn.execute(
                        text(f'DELETE FROM "{table}" WHERE {where_sql}'), where_params
                    )
                return {"row_count": result.rowcount}

            raise NodeError(f"Unknown operation: {op}")
        finally:
            engine.dispose()

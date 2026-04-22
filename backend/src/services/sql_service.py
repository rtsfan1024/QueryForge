from __future__ import annotations

from dataclasses import dataclass
from time import perf_counter

import psycopg
import sqlglot
from sqlglot import exp

from src.models.schemas import QueryError, QueryResult


@dataclass
class SQLService:
    def normalize_sql(self, sql: str) -> tuple[str, int]:
        parsed = sqlglot.parse_one(sql)
        if not isinstance(parsed, exp.Select):
            raise ValueError("Only SELECT statements are allowed")
        if parsed.args.get("limit") is None:
            parsed = parsed.limit(1000)
            return parsed.sql(dialect="postgres"), 1000
        return parsed.sql(dialect="postgres"), 0

    def validate_sql(self, sql: str) -> None:
        parsed = sqlglot.parse_one(sql)
        if not isinstance(parsed, exp.Select):
            raise ValueError("Only SELECT statements are allowed")

    def execute_sql(self, sql: str, dsn: str | None = None) -> QueryResult:
        self.validate_sql(sql)
        normalized_sql, applied = self.normalize_sql(sql)
        if dsn is None:
            return QueryResult(columns=[], rows=[], rowCount=0, appliedLimit=applied or 1000, durationMs=0, error=None)

        started = perf_counter()
        with psycopg.connect(dsn) as conn:
            with conn.cursor() as cur:
                cur.execute(normalized_sql)
                rows = cur.fetchall()
                column_names = [desc.name for desc in (cur.description or [])]
                columns = [{"name": name, "type": "unknown"} for name in column_names]

        duration_ms = int((perf_counter() - started) * 1000)
        result_rows = [
            {column_names[i]: value for i, value in enumerate(row)}
            for row in rows
        ]
        return QueryResult(
            columns=columns,
            rows=result_rows,
            rowCount=len(result_rows),
            appliedLimit=applied or 1000,
            durationMs=duration_ms,
            error=None,
        )

    def error(self, code: str, message: str) -> QueryResult:
        return QueryResult(columns=[], rows=[], rowCount=0, appliedLimit=0, durationMs=0, error=QueryError(code=code, message=message))

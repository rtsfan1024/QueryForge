from __future__ import annotations

from dataclasses import dataclass, field
from time import perf_counter

import pymysql
import sqlglot
from sqlglot import exp

from src.models.schemas import QueryError, QueryResult
from src.repositories.mysql_connection_factory import MySQLConnectionFactory
from src.services.sql_dialect_interface import ISQLDialect


@dataclass
class MySQLDialect(ISQLDialect):
    connection_factory: MySQLConnectionFactory = field(default_factory=MySQLConnectionFactory)

    def normalize_sql(self, sql: str) -> tuple[str, int]:
        parsed = sqlglot.parse_one(sql)
        if not isinstance(parsed, exp.Select):
            raise ValueError("Only SELECT statements are allowed")
        if parsed.args.get("limit") is None:
            parsed = parsed.limit(1000)
            return parsed.sql(dialect="mysql"), 1000
        return parsed.sql(dialect="mysql"), 0

    def validate_sql(self, sql: str) -> None:
        parsed = sqlglot.parse_one(sql)
        if not isinstance(parsed, exp.Select):
            raise ValueError("Only SELECT statements are allowed")

    def execute_sql(self, sql: str, dsn: str) -> QueryResult:
        self.validate_sql(sql)
        normalized_sql, applied = self.normalize_sql(sql)

        started = perf_counter()
        connection = self.connection_factory.create_connection(dsn)
        try:
            with connection.cursor() as cur:
                cur.execute(normalized_sql)
                rows = cur.fetchall()
                column_names = [desc[0] for desc in (cur.description or [])]
                columns = [{"name": name, "type": "unknown"} for name in column_names]
        finally:
            connection.close()

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

from __future__ import annotations

from dataclasses import dataclass

from src.models.schemas import DatabaseType, QueryError, QueryResult
from src.repositories.connection_factory import ConnectionFactory
from src.services.sql_dialect_factory import SQLDialectFactory
from src.services.sql_dialect_interface import ISQLDialect


@dataclass
class SQLService:
    def get_dialect(self, db_type: DatabaseType) -> ISQLDialect:
        return SQLDialectFactory.create(db_type)

    def normalize_sql(self, sql: str, db_type: DatabaseType = DatabaseType.postgresql) -> tuple[str, int]:
        dialect = self.get_dialect(db_type)
        return dialect.normalize_sql(sql)

    def validate_sql(self, sql: str, db_type: DatabaseType = DatabaseType.postgresql) -> None:
        dialect = self.get_dialect(db_type)
        dialect.validate_sql(sql)

    def execute_sql(self, sql: str, dsn: str | None = None, db_type: DatabaseType = DatabaseType.postgresql) -> QueryResult:
        dialect = self.get_dialect(db_type)
        dialect.validate_sql(sql)
        normalized_sql, applied = dialect.normalize_sql(sql)
        if dsn is None:
            return QueryResult(columns=[], rows=[], rowCount=0, appliedLimit=applied or 1000, durationMs=0, error=None)

        return dialect.execute_sql(sql, dsn)

    def error(self, code: str, message: str) -> QueryResult:
        return QueryResult(columns=[], rows=[], rowCount=0, appliedLimit=0, durationMs=0, error=QueryError(code=code, message=message))

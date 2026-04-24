from __future__ import annotations

from abc import ABC, abstractmethod

from src.models.schemas import QueryResult


class ISQLDialect(ABC):
    @abstractmethod
    def normalize_sql(self, sql: str) -> tuple[str, int]:
        """Return (normalized_sql, applied_limit). applied_limit=0 means no default limit was added."""
        ...

    @abstractmethod
    def validate_sql(self, sql: str) -> None:
        """Raise ValueError if the SQL is not a valid read-only SELECT."""
        ...

    @abstractmethod
    def execute_sql(self, sql: str, dsn: str) -> QueryResult: ...

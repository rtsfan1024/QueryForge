from __future__ import annotations

from src.models.schemas import DatabaseType
from src.services.mysql_dialect import MySQLDialect
from src.services.postgres_dialect import PostgreSQLDialect
from src.services.sql_dialect_interface import ISQLDialect


class SQLDialectFactory:
    _registry: dict[DatabaseType, type[ISQLDialect]] = {
        DatabaseType.postgresql: PostgreSQLDialect,
        DatabaseType.mysql: MySQLDialect,
    }

    @classmethod
    def register(cls, db_type: DatabaseType, dialect_cls: type[ISQLDialect]) -> None:
        cls._registry[db_type] = dialect_cls

    @classmethod
    def create(cls, db_type: DatabaseType) -> ISQLDialect:
        dialect_cls = cls._registry.get(db_type)
        if dialect_cls is None:
            raise ValueError(f"Unsupported database type: {db_type.value}")
        return dialect_cls()

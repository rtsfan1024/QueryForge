from __future__ import annotations

from src.models.schemas import DatabaseType
from src.repositories.introspector_interface import IDatabaseIntrospector
from src.repositories.mysql_introspection import MySQLIntrospector
from src.repositories.postgres_introspection import PostgresIntrospector


class IntrospectorFactory:
    _registry: dict[DatabaseType, type[IDatabaseIntrospector]] = {
        DatabaseType.postgresql: PostgresIntrospector,
        DatabaseType.mysql: MySQLIntrospector,
    }

    @classmethod
    def register(cls, db_type: DatabaseType, introspector_cls: type[IDatabaseIntrospector]) -> None:
        cls._registry[db_type] = introspector_cls

    @classmethod
    def create(cls, db_type: DatabaseType) -> IDatabaseIntrospector:
        introspector_cls = cls._registry.get(db_type)
        if introspector_cls is None:
            raise ValueError(f"Unsupported database type: {db_type.value}")
        return introspector_cls()

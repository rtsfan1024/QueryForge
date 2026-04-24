from __future__ import annotations

from src.models.schemas import DatabaseType
from src.repositories.connection_factory_interface import IDatabaseConnectionFactory
from src.repositories.mysql_connection_factory import MySQLConnectionFactory
from src.repositories.postgres_connection_factory import PostgresConnectionFactory


class ConnectionFactory:
    _registry: dict[DatabaseType, type[IDatabaseConnectionFactory]] = {
        DatabaseType.postgresql: PostgresConnectionFactory,
        DatabaseType.mysql: MySQLConnectionFactory,
    }

    @classmethod
    def register(cls, db_type: DatabaseType, factory_cls: type[IDatabaseConnectionFactory]) -> None:
        cls._registry[db_type] = factory_cls

    @classmethod
    def create(cls, db_type: DatabaseType) -> IDatabaseConnectionFactory:
        factory_cls = cls._registry.get(db_type)
        if factory_cls is None:
            raise ValueError(f"Unsupported database type: {db_type.value}")
        return factory_cls()

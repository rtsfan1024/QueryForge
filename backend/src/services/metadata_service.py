from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from uuid import uuid4

from src.models.schemas import ConnectionStatus, DatabaseConnection, SchemaMetadata
from src.repositories.postgres_introspection import PostgresIntrospector
from src.repositories.sqlite_store import SQLiteStore


@dataclass
class MetadataService:
    store: SQLiteStore
    introspector: PostgresIntrospector | None = None

    def save_connection(self, name: str, url: str, password: str | None = None, active: bool = True) -> DatabaseConnection:
        now = datetime.now(timezone.utc)
        connection = DatabaseConnection(
            id=str(uuid4()),
            name=name,
            url=url,
            status=ConnectionStatus.active if active else ConnectionStatus.error,
            lastConnectedAt=now if active else None,
            createdAt=now,
            updatedAt=now,
        )
        self.store.upsert_connection(connection)
        if active and self.introspector:
            self.introspector.test_connection(url, password=password)
        return connection

    def list_connections(self) -> list[DatabaseConnection]:
        return self.store.list_connections()

    def get_metadata(self, db_name: str) -> list[SchemaMetadata]:
        return self.store.list_schema_metadata(db_name)

    def refresh_metadata(self, db_name: str, url: str, password: str | None = None) -> list[SchemaMetadata]:
        introspector = self.introspector or PostgresIntrospector()
        metadata = introspector.fetch_schema(db_name, url, password=password)
        for item in metadata:
            self.store.upsert_schema_metadata(item)
        return metadata

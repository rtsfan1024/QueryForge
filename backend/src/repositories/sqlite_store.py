from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from uuid import uuid4

from src.models.schemas import ConnectionStatus, DatabaseConnection, ObjectType, SchemaMetadata

DB_PATH = Path("D:/Project/Cursor/w2/db_query/db_query.db")


class SQLiteStore:
    def __init__(self, path: Path = DB_PATH) -> None:
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.path)
        conn.row_factory = sqlite3.Row
        return conn

    def initialize(self) -> None:
        with self.connect() as conn:
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS database_connections (
                    id TEXT PRIMARY KEY,
                    name TEXT UNIQUE NOT NULL,
                    url TEXT NOT NULL,
                    status TEXT NOT NULL,
                    last_connected_at TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS schema_metadata (
                    id TEXT PRIMARY KEY,
                    db_name TEXT NOT NULL,
                    object_name TEXT NOT NULL,
                    object_type TEXT NOT NULL,
                    columns_json TEXT NOT NULL,
                    raw_metadata_json TEXT,
                    refreshed_at TEXT NOT NULL,
                    UNIQUE(db_name, object_name, object_type)
                );
                """
            )
            conn.commit()

    def upsert_connection(self, connection: DatabaseConnection) -> None:
        with self.connect() as conn:
            conn.execute(
                """
                INSERT INTO database_connections (id, name, url, status, last_connected_at, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(name) DO UPDATE SET
                  url=excluded.url,
                  status=excluded.status,
                  last_connected_at=excluded.last_connected_at,
                  updated_at=excluded.updated_at
                """,
                (
                    connection.id,
                    connection.name,
                    connection.url,
                    connection.status.value,
                    connection.lastConnectedAt.isoformat() if connection.lastConnectedAt else None,
                    connection.createdAt.isoformat(),
                    connection.updatedAt.isoformat(),
                ),
            )
            conn.commit()

    def list_connections(self) -> list[DatabaseConnection]:
        with self.connect() as conn:
            rows = conn.execute("SELECT * FROM database_connections ORDER BY created_at DESC").fetchall()
        return [self._row_to_connection(row) for row in rows]

    def get_connection(self, name: str) -> DatabaseConnection | None:
        with self.connect() as conn:
            row = conn.execute("SELECT * FROM database_connections WHERE name = ?", (name,)).fetchone()
        return self._row_to_connection(row) if row else None

    def upsert_schema_metadata(self, metadata: SchemaMetadata) -> None:
        with self.connect() as conn:
            conn.execute(
                """
                INSERT INTO schema_metadata (id, db_name, object_name, object_type, columns_json, raw_metadata_json, refreshed_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(db_name, object_name, object_type) DO UPDATE SET
                  columns_json=excluded.columns_json,
                  raw_metadata_json=excluded.raw_metadata_json,
                  refreshed_at=excluded.refreshed_at
                """,
                (
                    metadata.id,
                    metadata.dbName,
                    metadata.objectName,
                    metadata.objectType.value,
                    json.dumps(metadata.columnsJson, ensure_ascii=False),
                    json.dumps(metadata.rawMetadataJson, ensure_ascii=False) if metadata.rawMetadataJson is not None else None,
                    metadata.refreshedAt.isoformat(),
                ),
            )
            conn.commit()

    def list_schema_metadata(self, db_name: str) -> list[SchemaMetadata]:
        with self.connect() as conn:
            rows = conn.execute("SELECT * FROM schema_metadata WHERE db_name = ? ORDER BY object_type, object_name", (db_name,)).fetchall()
        return [self._row_to_schema(row) for row in rows]

    def _row_to_connection(self, row: sqlite3.Row) -> DatabaseConnection:
        from datetime import datetime

        return DatabaseConnection(
            id=row["id"],
            name=row["name"],
            url=row["url"],
            status=ConnectionStatus(row["status"]),
            lastConnectedAt=datetime.fromisoformat(row["last_connected_at"]) if row["last_connected_at"] else None,
            createdAt=datetime.fromisoformat(row["created_at"]),
            updatedAt=datetime.fromisoformat(row["updated_at"]),
        )

    def _row_to_schema(self, row: sqlite3.Row) -> SchemaMetadata:
        from datetime import datetime

        return SchemaMetadata(
            id=row["id"],
            dbName=row["db_name"],
            objectName=row["object_name"],
            objectType=ObjectType(row["object_type"]),
            columnsJson=json.loads(row["columns_json"]),
            rawMetadataJson=json.loads(row["raw_metadata_json"]) if row["raw_metadata_json"] else None,
            refreshedAt=datetime.fromisoformat(row["refreshed_at"]),
        )

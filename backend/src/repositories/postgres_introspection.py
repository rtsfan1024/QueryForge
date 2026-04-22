from __future__ import annotations

from dataclasses import dataclass
from urllib.parse import urlparse, urlunparse

import psycopg

from src.models.schemas import ObjectType, SchemaMetadata


@dataclass
class PostgresIntrospector:
    def _normalize_dsn(self, url: str, password: str | None = None) -> str:
        parsed = urlparse(url)
        if parsed.scheme not in {"postgres", "postgresql"}:
            raise ValueError("Only postgres URLs are supported")

        if password and parsed.username and not parsed.password:
            netloc = parsed.netloc
            userinfo, host = netloc.split("@", 1)
            if ":" not in userinfo:
                userinfo = f"{userinfo}:{password}"
                netloc = f"{userinfo}@{host}"
                parsed = parsed._replace(netloc=netloc)
        return urlunparse(parsed)

    def test_connection(self, url: str, password: str | None = None) -> None:
        dsn = self._normalize_dsn(url, password=password)
        with psycopg.connect(dsn) as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT 1")

    def fetch_schema(self, db_name: str, url: str, password: str | None = None) -> list[SchemaMetadata]:
        dsn = self._normalize_dsn(url, password=password)
        from datetime import datetime, timezone
        from uuid import uuid4

        now = datetime.now(timezone.utc)
        with psycopg.connect(dsn) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT
                        t.table_name,
                        t.table_type,
                        c.column_name,
                        c.data_type,
                        c.ordinal_position,
                        tc.constraint_type,
                        ccu.table_name AS foreign_table_name,
                        ccu.column_name AS foreign_column_name
                    FROM information_schema.tables AS t
                    JOIN information_schema.columns AS c
                      ON c.table_name = t.table_name
                     AND c.table_schema = t.table_schema
                    LEFT JOIN information_schema.key_column_usage AS kcu
                      ON kcu.table_name = c.table_name
                     AND kcu.column_name = c.column_name
                     AND kcu.table_schema = c.table_schema
                    LEFT JOIN information_schema.table_constraints AS tc
                      ON tc.constraint_name = kcu.constraint_name
                     AND tc.table_schema = kcu.table_schema
                     AND tc.constraint_type = 'FOREIGN KEY'
                    LEFT JOIN information_schema.constraint_column_usage AS ccu
                      ON ccu.constraint_name = tc.constraint_name
                     AND ccu.table_schema = tc.table_schema
                    WHERE t.table_schema NOT IN ('pg_catalog', 'information_schema')
                    ORDER BY t.table_name, c.ordinal_position
                    """
                )
                rows = cur.fetchall()

        tables: dict[str, dict[str, object]] = {}
        for row in rows:
            table_name = row[0]
            table_type = row[1]
            column_name = row[2]
            data_type = row[3]
            constraint_type = row[5]
            foreign_table_name = row[6]
            foreign_column_name = row[7]

            entry = tables.setdefault(
                table_name,
                {
                    "table_type": table_type,
                    "columns": [],
                    "relationships": [],
                },
            )
            entry["columns"].append({"name": column_name, "type": data_type})
            if constraint_type == "FOREIGN KEY" and foreign_table_name and foreign_column_name:
                entry["relationships"].append(
                    {
                        "column": column_name,
                        "references": f"{foreign_table_name}.{foreign_column_name}",
                    }
                )

        metadata: list[SchemaMetadata] = []
        for table_name, info in tables.items():
            table_type = str(info["table_type"])
            object_type = ObjectType.view if table_type.lower().startswith("view") else ObjectType.table
            metadata.append(
                SchemaMetadata(
                    id=str(uuid4()),
                    dbName=db_name,
                    objectName=table_name,
                    objectType=object_type,
                    columnsJson=info["columns"],
                    rawMetadataJson={
                        "tableType": table_type,
                        "relationships": info["relationships"],
                    },
                    refreshedAt=now,
                )
            )
        return metadata

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from urllib.parse import urlparse, urlunparse
from uuid import uuid4

import pymysql

from src.models.schemas import ObjectType, SchemaMetadata
from src.repositories.introspector_interface import IDatabaseIntrospector


@dataclass
class MySQLIntrospector(IDatabaseIntrospector):
    def _parse_dsn(self, url: str, password: str | None = None) -> dict[str, object]:
        parsed = urlparse(url)
        if parsed.scheme not in {"mysql", "mysql+pymysql"}:
            raise ValueError("Only mysql URLs are supported")

        host = parsed.hostname or "localhost"
        port = parsed.port or 3306
        user = parsed.username or "root"
        db_name = parsed.path.lstrip("/") or ""
        pw = parsed.password or password or ""

        return {
            "host": host,
            "port": port,
            "user": user,
            "password": pw,
            "database": db_name,
        }

    def _normalize_dsn(self, url: str, password: str | None = None) -> str:
        parsed = urlparse(url)
        if password and parsed.username and not parsed.password:
            netloc = parsed.netloc
            userinfo, host = netloc.split("@", 1)
            if ":" not in userinfo:
                userinfo = f"{userinfo}:{password}"
                netloc = f"{userinfo}@{host}"
                parsed = parsed._replace(netloc=netloc)
        return urlunparse(parsed)

    def test_connection(self, url: str, password: str | None = None) -> None:
        params = self._parse_dsn(url, password=password)
        connection = pymysql.connect(**params)  # type: ignore[arg-type]
        try:
            with connection.cursor() as cur:
                cur.execute("SELECT 1")
        finally:
            connection.close()

    def fetch_schema(self, db_name: str, url: str, password: str | None = None) -> list[SchemaMetadata]:
        params = self._parse_dsn(url, password=password)
        now = datetime.now(timezone.utc)

        connection = pymysql.connect(**params)  # type: ignore[arg-type]
        try:
            with connection.cursor() as cur:
                cur.execute(
                    """
                    SELECT
                        t.TABLE_NAME,
                        t.TABLE_TYPE,
                        c.COLUMN_NAME,
                        c.DATA_TYPE,
                        c.ORDINAL_POSITION,
                        tc.CONSTRAINT_TYPE,
                        kcu.REFERENCED_TABLE_NAME,
                        kcu.REFERENCED_COLUMN_NAME
                    FROM information_schema.TABLES AS t
                    JOIN information_schema.COLUMNS AS c
                      ON c.TABLE_NAME = t.TABLE_NAME
                     AND c.TABLE_SCHEMA = t.TABLE_SCHEMA
                    LEFT JOIN information_schema.KEY_COLUMN_USAGE AS kcu
                      ON kcu.TABLE_NAME = c.TABLE_NAME
                     AND kcu.COLUMN_NAME = c.COLUMN_NAME
                     AND kcu.TABLE_SCHEMA = c.TABLE_SCHEMA
                     AND kcu.REFERENCED_TABLE_NAME IS NOT NULL
                    LEFT JOIN information_schema.TABLE_CONSTRAINTS AS tc
                      ON tc.CONSTRAINT_NAME = kcu.CONSTRAINT_NAME
                     AND tc.TABLE_SCHEMA = kcu.TABLE_SCHEMA
                     AND tc.CONSTRAINT_TYPE = 'FOREIGN KEY'
                    WHERE t.TABLE_SCHEMA = %s
                    ORDER BY t.TABLE_NAME, c.ORDINAL_POSITION
                    """,
                    (params["database"],),
                )
                rows = cur.fetchall()
        finally:
            connection.close()

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
            object_type = ObjectType.view if "VIEW" in table_type.upper() else ObjectType.table
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

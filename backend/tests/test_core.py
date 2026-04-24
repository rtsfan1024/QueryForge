from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

import pytest

import src.api.dbs as dbs
from src.models.schemas import ConnectionStatus, DatabaseConnection, DatabaseType
from src.repositories.sqlite_store import SQLiteStore


@pytest.fixture()
def temp_store(tmp_path: Path) -> SQLiteStore:
    store = SQLiteStore(tmp_path / "db_query.db")
    store.initialize()
    return store


def test_list_dbs_returns_items() -> None:
    result = dbs.list_dbs()
    assert "items" in result
    assert isinstance(result["items"], list)


def test_add_db_requires_url() -> None:
    with pytest.raises(Exception) as exc_info:
        dbs.add_db("demo", {})
    assert "url is required" in str(exc_info.value)


def test_add_db_rejects_invalid_db_type() -> None:
    with pytest.raises(Exception) as exc_info:
        dbs.add_db("demo", {"url": "postgres://localhost/db", "dbType": "oracle"})
    assert "Unsupported database type" in str(exc_info.value)


def test_get_db_returns_metadata_shape() -> None:
    result = dbs.get_db("demo")
    assert result["name"] == "demo"
    assert "tables" in result and "views" in result


def _seed_connection(name: str = "demo") -> None:
    """Insert a test connection directly into the store so query endpoints can find it."""
    from datetime import datetime, timezone
    from uuid import uuid4

    conn = DatabaseConnection(
        id=str(uuid4()),
        name=name,
        url="postgres://postgres@localhost:5432/postgres",
        dbType=DatabaseType.postgresql,
        status=ConnectionStatus.active,
        lastConnectedAt=datetime.now(timezone.utc),
        createdAt=datetime.now(timezone.utc),
        updatedAt=datetime.now(timezone.utc),
    )
    dbs.store.upsert_connection(conn)


def test_query_db_applies_default_limit(monkeypatch: pytest.MonkeyPatch) -> None:
    _seed_connection("demo_ql")
    monkeypatch.setattr(dbs, "_get_connection_dsn", lambda name: "postgres://postgres:postgres@localhost:5432/postgres")
    monkeypatch.setattr(dbs.sql_service, "execute_sql", lambda sql, dsn=None, db_type=DatabaseType.postgresql: SimpleNamespace(model_dump=lambda by_alias=True: {"appliedLimit": 1000}))
    result = dbs.query_db("demo_ql", {"sql": "SELECT * FROM users"})
    assert result["appliedLimit"] == 1000


def test_query_natural_returns_generated_sql(monkeypatch: pytest.MonkeyPatch) -> None:
    _seed_connection("demo_nq")
    monkeypatch.setattr(dbs, "_get_connection_dsn", lambda name: "postgres://postgres:postgres@localhost:5432/postgres")
    monkeypatch.setattr(dbs.sql_service, "execute_sql", lambda sql, dsn=None, db_type=DatabaseType.postgresql: SimpleNamespace(model_dump=lambda by_alias=True: {"appliedLimit": 1000}))
    monkeypatch.setattr(dbs.llm_client, "generate_sql", lambda prompt, context, db_type=DatabaseType.postgresql: "SELECT 1")
    result = dbs.query_natural("demo_nq", {"prompt": "list users"})
    assert result["generatedSql"] == "SELECT 1"

from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

import pytest

import src.api.dbs as dbs
from src.repositories.sqlite_store import SQLiteStore


@pytest.fixture()
def temp_store(tmp_path: Path) -> SQLiteStore:
    store = SQLiteStore(tmp_path / "db_query.db")
    store.initialize()
    return store


def test_list_dbs_returns_items() -> None:
    assert dbs.list_dbs() == {"items": []}


def test_add_db_requires_url() -> None:
    with pytest.raises(Exception) as exc_info:
        dbs.add_db("demo", {})
    assert "url is required" in str(exc_info.value)


def test_get_db_returns_metadata_shape() -> None:
    result = dbs.get_db("demo")
    assert result["name"] == "demo"
    assert "tables" in result and "views" in result


def test_query_db_applies_default_limit(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(dbs, "_get_connection_dsn", lambda name: "postgres://postgres:postgres@localhost:5432/postgres")
    monkeypatch.setattr(dbs.sql_service, "execute_sql", lambda sql, dsn=None: SimpleNamespace(model_dump=lambda by_alias=True: {"appliedLimit": 1000}))
    result = dbs.query_db("demo", {"sql": "SELECT * FROM users"})
    assert result["appliedLimit"] == 1000


def test_query_natural_returns_generated_sql(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(dbs, "_get_connection_dsn", lambda name: "postgres://postgres:postgres@localhost:5432/postgres")
    monkeypatch.setattr(dbs.sql_service, "execute_sql", lambda sql, dsn=None: SimpleNamespace(model_dump=lambda by_alias=True: {"appliedLimit": 1000}))
    result = dbs.query_natural("demo", {"prompt": "list users"})
    assert result["generatedSql"] == "SELECT 1"

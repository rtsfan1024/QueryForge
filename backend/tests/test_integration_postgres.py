from __future__ import annotations

import os

import pytest

from src.api import dbs
from src.repositories.postgres_introspection import PostgresIntrospector
from src.services.sql_service import SQLService


@pytest.mark.integration
@pytest.mark.skipif(
    not os.getenv("DB_QUERY_POSTGRES_DSN"),
    reason="DB_QUERY_POSTGRES_DSN is required for real PostgreSQL integration tests",
)
def test_postgres_connection_and_metadata_fetch() -> None:
    dsn = os.environ["DB_QUERY_POSTGRES_DSN"]
    introspector = PostgresIntrospector()
    introspector.test_connection(dsn)
    metadata = introspector.fetch_schema("demo", dsn)
    assert isinstance(metadata, list)
    assert all(item.objectType.value in {"table", "view"} for item in metadata)


@pytest.mark.integration
@pytest.mark.skipif(
    not os.getenv("DB_QUERY_POSTGRES_DSN"),
    reason="DB_QUERY_POSTGRES_DSN is required for real PostgreSQL integration tests",
)
def test_real_sql_execution_against_postgres() -> None:
    dsn = os.environ["DB_QUERY_POSTGRES_DSN"]
    service = SQLService()
    result = service.execute_sql("SELECT 1 AS value", dsn=dsn)
    assert result.rowCount >= 1
    assert result.appliedLimit == 1000
    assert result.columns is not None
    assert result.rows is not None
    assert result.rows[0]["value"] == 1


@pytest.mark.integration
@pytest.mark.skipif(
    not os.getenv("DB_QUERY_POSTGRES_DSN"),
    reason="DB_QUERY_POSTGRES_DSN is required for real PostgreSQL integration tests",
)
def test_sql_rejects_non_select_statement() -> None:
    service = SQLService()
    with pytest.raises(ValueError, match="Only SELECT statements are allowed"):
        service.validate_sql("UPDATE users SET name = 'x'")


@pytest.mark.integration
@pytest.mark.skipif(
    not os.getenv("DB_QUERY_POSTGRES_DSN"),
    reason="DB_QUERY_POSTGRES_DSN is required for real PostgreSQL integration tests",
)
def test_natural_query_pipeline_returns_result_shape(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(dbs, "_get_connection_dsn", lambda name: os.environ["DB_QUERY_POSTGRES_DSN"])
    monkeypatch.setattr(dbs, "sql_service", SQLService())
    result = dbs.query_natural("demo", {"prompt": "查询前一条数据"})
    assert result["generatedSql"].startswith("SELECT")
    assert "result" in result
    assert "rows" in result["result"]

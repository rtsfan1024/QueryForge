"""Integration tests for MySQL support.

These tests require a running MySQL instance and are skipped if
the DB_QUERY_MYSQL_TEST_URL environment variable is not set.
"""

from __future__ import annotations

import os
import pytest

from src.models.schemas import DatabaseType
from src.repositories.mysql_introspection import MySQLIntrospector
from src.services.mysql_dialect import MySQLDialect


MYSQL_TEST_URL = os.getenv("DB_QUERY_MYSQL_TEST_URL", "")
MYSQL_TEST_PASSWORD = os.getenv("DB_QUERY_MYSQL_PASSWORD", "")

skip_no_mysql = pytest.mark.skipif(
    not MYSQL_TEST_URL,
    reason="DB_QUERY_MYSQL_TEST_URL not set — MySQL integration tests disabled",
)


@skip_no_mysql
class TestMySQLIntrospector:
    def test_connection(self) -> None:
        introspector = MySQLIntrospector()
        introspector.test_connection(MYSQL_TEST_URL, password=MYSQL_TEST_PASSWORD)

    def test_fetch_schema(self) -> None:
        introspector = MySQLIntrospector()
        metadata = introspector.fetch_schema("test_db", MYSQL_TEST_URL, password=MYSQL_TEST_PASSWORD)
        assert isinstance(metadata, list)

    def test_invalid_url(self) -> None:
        introspector = MySQLIntrospector()
        with pytest.raises(ValueError, match="mysql"):
            introspector.test_connection("postgres://user@localhost/db")


@skip_no_mysql
class TestMySQLDialect:
    def test_normalize_select_no_limit(self) -> None:
        dialect = MySQLDialect()
        sql, applied = dialect.normalize_sql("SELECT * FROM users")
        assert "LIMIT" in sql.upper()
        assert applied == 1000

    def test_normalize_select_with_limit(self) -> None:
        dialect = MySQLDialect()
        sql, applied = dialect.normalize_sql("SELECT * FROM users LIMIT 10")
        assert applied == 0

    def test_validate_non_select_rejected(self) -> None:
        dialect = MySQLDialect()
        with pytest.raises(ValueError, match="SELECT"):
            dialect.validate_sql("DELETE FROM users")

    def test_execute_sql(self) -> None:
        dialect = MySQLDialect()
        result = dialect.execute_sql("SELECT 1 AS val", MYSQL_TEST_URL)
        assert result.rowCount >= 1
        assert result.error is None


class TestDatabaseTypeEnum:
    def test_mysql_value(self) -> None:
        assert DatabaseType.mysql.value == "mysql"

    def test_postgresql_value(self) -> None:
        assert DatabaseType.postgresql.value == "postgresql"

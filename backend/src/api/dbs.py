from __future__ import annotations

import os
from fastapi import APIRouter, HTTPException
import sqlglot
from urllib.parse import urlparse, urlunparse

from src.llm.client import LLMClient
from src.models.schemas import DatabaseType
from src.repositories.connection_factory import ConnectionFactory
from src.repositories.introspector_factory import IntrospectorFactory
from src.repositories.sqlite_store import SQLiteStore
from src.services.metadata_service import MetadataService
from src.services.sql_dialect_factory import SQLDialectFactory
from src.services.sql_service import SQLService

router = APIRouter(prefix="/api/v1/dbs", tags=["dbs"])
store = SQLiteStore()
store.initialize()
metadata_service = MetadataService(store)
sql_service = SQLService()
llm_client = LLMClient()


def _get_default_password(db_type: DatabaseType = DatabaseType.postgresql) -> str | None:
    if db_type == DatabaseType.mysql:
        return os.getenv("DB_QUERY_MYSQL_PASSWORD") or os.getenv("MYSQL_PASSWORD") or ""
    return os.getenv("DB_QUERY_POSTGRES_PASSWORD") or os.getenv("POSTGRES_PASSWORD") or "postgres"


def _get_connection_dsn(name: str) -> str:
    connection = store.get_connection(name)
    if connection is None:
        raise HTTPException(status_code=404, detail="database connection not found")
    dsn = _apply_password_to_dsn(connection.url, _get_default_password(connection.dbType))
    return dsn


def _apply_password_to_dsn(url: str, password: str | None) -> str:
    if not password:
        return url
    parsed = urlparse(url)
    if parsed.password:
        return url
    if not parsed.username:
        return url
    netloc = parsed.netloc
    userinfo, host = netloc.split("@", 1)
    if ":" not in userinfo:
        userinfo = f"{userinfo}:{password}"
        parsed = parsed._replace(netloc=f"{userinfo}@{host}")
    return urlunparse(parsed)


def _build_schema_context(name: str) -> str:
    metadata = metadata_service.get_metadata(name)
    if not metadata:
        return "暂无可用 Schema。"
    lines = []
    for item in metadata:
        columns = ", ".join(f"{col['name']}:{col['type']}" for col in item.columnsJson)
        lines.append(f"表 {item.objectName} ({item.objectType.value})")
        lines.append(f"- 列: {columns}")
        relationships = []
        raw_metadata = item.rawMetadataJson or {}
        for relation in raw_metadata.get("relationships", []):
            relationships.append(f"- 关系: {relation['column']} -> {relation['references']}")
        lines.extend(relationships)
    return "\n".join(lines)


def _extract_referenced_columns(sql: str) -> set[str]:
    try:
        parsed = sqlglot.parse_one(sql)
    except sqlglot.errors.ParseError:
        return set()
    return {
        column.name
        for column in parsed.find_all(sqlglot.exp.Column)
        if column.name != "*"
    }


def _validate_generated_sql_against_schema(name: str, sql: str) -> None:
    metadata = metadata_service.get_metadata(name)
    allowed_columns = {column["name"] for item in metadata for column in item.columnsJson}
    referenced_columns = _extract_referenced_columns(sql)
    unknown_columns = referenced_columns - allowed_columns
    if unknown_columns:
        raise HTTPException(
            status_code=400,
            detail=f"generated sql uses unknown columns: {', '.join(sorted(unknown_columns))}",
        )


def _natural_query_payload(name: str, prompt: str, db_type: DatabaseType) -> dict[str, object]:
    context = _build_schema_context(name)
    generated_sql = llm_client.generate_sql(prompt=prompt, context=context, db_type=db_type)
    try:
        _validate_generated_sql_against_schema(name, generated_sql)
    except HTTPException as exc:
        return {
            "generatedSql": generated_sql,
            "result": None,
            "validationError": str(exc.detail),
            "executionError": None,
        }

    try:
        result = sql_service.execute_sql(generated_sql, dsn=_get_connection_dsn(name), db_type=db_type)
        return {
            "generatedSql": generated_sql,
            "result": result.model_dump(by_alias=True),
            "validationError": None,
            "executionError": None,
        }
    except (ValueError, sqlglot.errors.ParseError) as exc:
        return {
            "generatedSql": generated_sql,
            "result": None,
            "validationError": None,
            "executionError": str(exc),
        }
    except Exception as exc:
        return {
            "generatedSql": generated_sql,
            "result": None,
            "validationError": None,
            "executionError": str(exc),
        }


@router.get("")
def list_dbs() -> dict[str, list[dict[str, str]]]:
    items = [
        {
            "name": connection.name,
            "dbType": connection.dbType.value,
            "status": connection.status.value,
            "lastConnectedAt": connection.lastConnectedAt.isoformat() if connection.lastConnectedAt else None,
        }
        for connection in metadata_service.list_connections()
    ]
    return {"items": items}


@router.post("/{name}")
def add_db(name: str, payload: dict[str, str]) -> dict[str, str]:
    url = payload.get("url", "")
    db_type_str = payload.get("dbType", "postgresql")
    try:
        db_type = DatabaseType(db_type_str)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Unsupported database type: {db_type_str}")
    password = payload.get("password") or _get_default_password(db_type)
    if not url:
        raise HTTPException(status_code=400, detail="url is required")
    dsn = _apply_password_to_dsn(url, password)
    try:
        connection = metadata_service.save_connection(name, dsn, password=password, active=True, db_type=db_type)
        metadata_service.refresh_metadata(name, dsn, password=password, db_type=db_type)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {"name": connection.name, "status": connection.status.value, "url": connection.url, "dbType": connection.dbType.value}


@router.get("/{name}")
def get_db(name: str) -> dict[str, object]:
    metadata = metadata_service.get_metadata(name)
    return {
        "name": name,
        "tables": [item.model_dump(by_alias=True) for item in metadata if item.objectType.value == "table"],
        "views": [item.model_dump(by_alias=True) for item in metadata if item.objectType.value == "view"],
    }


@router.post("/{name}/query")
def query_db(name: str, payload: dict[str, str]) -> dict[str, object]:
    sql = payload.get("sql", "")
    if not sql:
        raise HTTPException(status_code=400, detail="sql is required")
    connection = store.get_connection(name)
    if connection is None:
        raise HTTPException(status_code=404, detail="database connection not found")
    db_type = connection.dbType
    try:
        result = sql_service.execute_sql(sql, dsn=_get_connection_dsn(name), db_type=db_type)
    except (ValueError, sqlglot.errors.ParseError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return result.model_dump(by_alias=True)


@router.post("/{name}/query/natural")
def query_natural(name: str, payload: dict[str, str]) -> dict[str, object]:
    prompt = payload.get("prompt", "")
    if not prompt:
        raise HTTPException(status_code=400, detail="prompt is required")
    connection = store.get_connection(name)
    if connection is None:
        raise HTTPException(status_code=404, detail="database connection not found")
    db_type = connection.dbType
    return _natural_query_payload(name, prompt, db_type)

from __future__ import annotations

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field, HttpUrl


class ConnectionStatus(str, Enum):
    active = "active"
    error = "error"


class DatabaseType(str, Enum):
    postgresql = "postgresql"
    mysql = "mysql"


class ObjectType(str, Enum):
    table = "table"
    view = "view"


class DatabaseConnection(BaseModel):
    id: str
    name: str
    url: str
    dbType: DatabaseType = DatabaseType.postgresql
    status: ConnectionStatus
    lastConnectedAt: datetime | None = None
    createdAt: datetime
    updatedAt: datetime


class SchemaMetadata(BaseModel):
    id: str
    dbName: str
    objectName: str
    objectType: ObjectType
    columnsJson: list[dict[str, str]]
    rawMetadataJson: dict[str, object] | None = None
    refreshedAt: datetime


class QueryRequest(BaseModel):
    dbName: str
    sourceType: str = Field(pattern="^(manual|natural)$")
    sql: str
    prompt: str | None = None
    normalizedSql: str
    appliedDefaultLimit: bool
    createdAt: datetime


class QueryError(BaseModel):
    code: str
    message: str


class QueryResult(BaseModel):
    columns: list[dict[str, object]]
    rows: list[dict[str, object]]
    rowCount: int
    appliedLimit: int
    durationMs: int
    error: QueryError | None = None


class NLPrompt(BaseModel):
    dbName: str
    prompt: str
    contextSnapshot: dict[str, object]
    generatedSql: str
    createdAt: datetime

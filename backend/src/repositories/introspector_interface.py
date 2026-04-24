from __future__ import annotations

from abc import ABC, abstractmethod

from src.models.schemas import SchemaMetadata


class IDatabaseIntrospector(ABC):
    @abstractmethod
    def test_connection(self, url: str, password: str | None = None) -> None: ...

    @abstractmethod
    def fetch_schema(self, db_name: str, url: str, password: str | None = None) -> list[SchemaMetadata]: ...

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class IDatabaseConnectionFactory(ABC):
    @abstractmethod
    def create_connection(self, dsn: str) -> Any:
        """Create and return a raw database connection from the given DSN."""
        ...

    @abstractmethod
    def normalize_dsn(self, url: str, password: str | None = None) -> str:
        """Normalize the URL/DSN, injecting password if needed."""
        ...

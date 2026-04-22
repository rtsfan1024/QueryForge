from __future__ import annotations

from dataclasses import dataclass

from src.repositories.sqlite_store import SQLiteStore


@dataclass
class DatabaseService:
    store: SQLiteStore

    def initialize(self) -> None:
        self.store.initialize()

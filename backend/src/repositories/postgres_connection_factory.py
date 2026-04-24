from __future__ import annotations

from dataclasses import dataclass
from urllib.parse import urlparse, urlunparse
from typing import Any

import psycopg

from src.repositories.connection_factory_interface import IDatabaseConnectionFactory


@dataclass
class PostgresConnectionFactory(IDatabaseConnectionFactory):
    def create_connection(self, dsn: str) -> Any:
        return psycopg.connect(dsn)

    def normalize_dsn(self, url: str, password: str | None = None) -> str:
        parsed = urlparse(url)
        if parsed.scheme not in {"postgres", "postgresql"}:
            raise ValueError("Only postgres URLs are supported")

        if password and parsed.username and not parsed.password:
            netloc = parsed.netloc
            userinfo, host = netloc.split("@", 1)
            if ":" not in userinfo:
                userinfo = f"{userinfo}:{password}"
                netloc = f"{userinfo}@{host}"
                parsed = parsed._replace(netloc=netloc)
        return urlunparse(parsed)

from __future__ import annotations

from dataclasses import dataclass
from urllib.parse import urlparse, urlunparse
from typing import Any

import pymysql

from src.repositories.connection_factory_interface import IDatabaseConnectionFactory


@dataclass
class MySQLConnectionFactory(IDatabaseConnectionFactory):
    def create_connection(self, dsn: str) -> Any:
        params = self._parse_dsn(dsn)
        return pymysql.connect(**params)  # type: ignore[arg-type]

    def normalize_dsn(self, url: str, password: str | None = None) -> str:
        parsed = urlparse(url)
        if parsed.scheme not in {"mysql", "mysql+pymysql"}:
            raise ValueError("Only mysql URLs are supported")
        if password and parsed.username and not parsed.password:
            netloc = parsed.netloc
            userinfo, host = netloc.split("@", 1)
            if ":" not in userinfo:
                userinfo = f"{userinfo}:{password}"
                netloc = f"{userinfo}@{host}"
                parsed = parsed._replace(netloc=netloc)
        return urlunparse(parsed)

    def _parse_dsn(self, url: str, password: str | None = None) -> dict[str, object]:
        parsed = urlparse(url)
        host = parsed.hostname or "localhost"
        port = parsed.port or 3306
        user = parsed.username or "root"
        db_name = parsed.path.lstrip("/") or ""
        pw = parsed.password or password or ""
        return {
            "host": host,
            "port": port,
            "user": user,
            "password": pw,
            "database": db_name,
        }

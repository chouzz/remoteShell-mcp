"""Persistent host storage for the RemoteShell MCP server.

This module is intentionally simple: it stores SSH connection metadata in a
single JSON file at `~/.config/remoteshell/hosts.json` so the LLM can manage
servers via tools (save/remove/list) without requiring user-side configuration.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Literal, Optional


AuthType = Literal["password", "private_key"]


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def default_hosts_path() -> Path:
    """Return the canonical hosts.json path."""
    return Path.home() / ".config" / "remoteshell" / "hosts.json"


@dataclass
class ServerConfig:
    """Configuration for a single server.

    Notes:
        - `credential` is stored as either `password` or `private_key` depending
          on `auth_type`.
        - `last_connected` is an ISO-8601 timestamp in UTC when a successful SSH
          connection was established.
    """

    connection_id: str
    host: str
    user: str
    port: int = 22
    auth_type: AuthType = "password"
    password: Optional[str] = None
    private_key: Optional[str] = None
    last_connected: Optional[str] = None

    def validate(self) -> None:
        if not self.connection_id:
            raise ValueError("connection_id is required")
        if not self.host:
            raise ValueError("host is required")
        if not self.user:
            raise ValueError("user is required")
        if self.port <= 0 or self.port > 65535:
            raise ValueError("port must be in range 1..65535")
        if self.auth_type not in ("password", "private_key"):
            raise ValueError("auth_type must be 'password' or 'private_key'")
        if self.auth_type == "password" and not self.password:
            raise ValueError("credential (password) is required for password auth")
        if self.auth_type == "private_key" and not self.private_key:
            raise ValueError("credential (private_key) is required for private_key auth")

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ServerConfig":
        return cls(
            connection_id=data.get("connection_id", data.get("id", "")),
            host=data.get("host", ""),
            user=data.get("user", ""),
            port=int(data.get("port", 22)),
            auth_type=data.get("auth_type", "password"),
            password=data.get("password"),
            private_key=data.get("private_key"),
            last_connected=data.get("last_connected"),
        )

    def to_dict(self) -> Dict[str, Any]:
        data: Dict[str, Any] = {
            "connection_id": self.connection_id,
            "host": self.host,
            "user": self.user,
            "port": self.port,
            "auth_type": self.auth_type,
            "last_connected": self.last_connected,
        }
        if self.auth_type == "password":
            data["password"] = self.password
        if self.auth_type == "private_key":
            data["private_key"] = self.private_key
        return data


class HostStore:
    """A small JSON-backed store for server configs."""

    def __init__(self, path: Optional[Path] = None):
        self.path = path or default_hosts_path()

    def _ensure_dir(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def _load_raw(self) -> Dict[str, Any]:
        if not self.path.exists():
            return {"version": 1, "servers": {}}
        try:
            with self.path.open("r", encoding="utf-8") as f:
                data = json.load(f)
        except json.JSONDecodeError:
            # If the file is corrupted, preserve it and start fresh.
            backup = self.path.with_suffix(self.path.suffix + ".corrupt")
            try:
                self.path.replace(backup)
            except Exception:
                pass
            return {"version": 1, "servers": {}}
        if not isinstance(data, dict):
            return {"version": 1, "servers": {}}
        data.setdefault("version", 1)
        data.setdefault("servers", {})
        if not isinstance(data["servers"], dict):
            data["servers"] = {}
        return data

    def _save_raw(self, data: Dict[str, Any]) -> None:
        self._ensure_dir()
        tmp = self.path.with_suffix(self.path.suffix + ".tmp")
        with tmp.open("w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        tmp.replace(self.path)
        # Best-effort permissions hardening on POSIX.
        try:
            os.chmod(self.path, 0o600)
        except Exception:
            pass

    def list(self) -> List[ServerConfig]:
        data = self._load_raw()
        servers: Dict[str, Any] = data.get("servers", {})
        configs: List[ServerConfig] = []
        for _id, payload in servers.items():
            if not isinstance(payload, dict):
                continue
            payload = {"connection_id": _id, **payload}
            try:
                cfg = ServerConfig.from_dict(payload)
                cfg.validate()
            except Exception:
                # Skip invalid entries (manual edits happen).
                continue
            configs.append(cfg)
        return sorted(configs, key=lambda c: c.connection_id)

    def get(self, connection_id: str) -> Optional[ServerConfig]:
        data = self._load_raw()
        payload = data.get("servers", {}).get(connection_id)
        if not isinstance(payload, dict):
            return None
        try:
            cfg = ServerConfig.from_dict({"connection_id": connection_id, **payload})
            cfg.validate()
            return cfg
        except Exception:
            return None

    def upsert(
        self,
        *,
        connection_id: str,
        host: str,
        user: str,
        port: Optional[int] = None,
        auth_type: AuthType,
        credential: str,
    ) -> ServerConfig:
        data = self._load_raw()
        servers: Dict[str, Any] = data.get("servers", {})
        existing = servers.get(connection_id)
        last_connected = None
        existing_port: int = 22
        if isinstance(existing, dict):
            last_connected = existing.get("last_connected")
            try:
                existing_port = int(existing.get("port", 22))
            except Exception:
                existing_port = 22

        chosen_port = existing_port if port is None else int(port)

        cfg = ServerConfig(
            connection_id=connection_id,
            host=host,
            user=user,
            port=chosen_port,
            auth_type=auth_type,
            password=credential if auth_type == "password" else None,
            private_key=credential if auth_type == "private_key" else None,
        )
        cfg.validate()

        cfg.last_connected = last_connected
        payload = cfg.to_dict()
        payload.pop("connection_id", None)  # connection_id is stored as the dict key
        servers[connection_id] = payload
        data["servers"] = servers
        self._save_raw(data)
        return cfg

    def remove(self, connection_id: str) -> bool:
        data = self._load_raw()
        servers: Dict[str, Any] = data.get("servers", {})
        if connection_id not in servers:
            return False
        del servers[connection_id]
        data["servers"] = servers
        self._save_raw(data)
        return True

    def touch_last_connected(self, connection_id: str, *, timestamp: Optional[str] = None) -> None:
        data = self._load_raw()
        servers: Dict[str, Any] = data.get("servers", {})
        payload = servers.get(connection_id)
        if not isinstance(payload, dict):
            return
        payload["last_connected"] = timestamp or _utc_now_iso()
        servers[connection_id] = payload
        data["servers"] = servers
        self._save_raw(data)



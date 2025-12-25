"""Tests for ConnectionManager behavior without real SSH."""

from __future__ import annotations

from pathlib import Path

import pytest

from remoteshell_mcp.connection_manager import ConnectionManager
from remoteshell_mcp.host_store import HostStore
from remoteshell_mcp.ssh_client import RemoteSSHClient


def test_connection_manager_connects_and_updates_last_connected(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    store = HostStore(path=tmp_path / "hosts.json")
    store.upsert(
        connection_id="srv1",
        host="1.2.3.4",
        user="root",
        port=2222,
        auth_type="password",
        credential="secret",
    )

    # Avoid real SSH: pretend connect succeeded and client is connected.
    monkeypatch.setattr(RemoteSSHClient, "connect", lambda self: None)
    monkeypatch.setattr(RemoteSSHClient, "is_connected", lambda self: True)

    manager = ConnectionManager(store)
    client = manager.get_or_create_connection("srv1")
    assert isinstance(client, RemoteSSHClient)
    assert client.port == 2222

    cfg = store.get("srv1")
    assert cfg is not None
    assert cfg.last_connected is not None


def test_connection_manager_unknown_id(tmp_path: Path):
    store = HostStore(path=tmp_path / "hosts.json")
    manager = ConnectionManager(store)
    with pytest.raises(ValueError):
        manager.get_or_create_connection("missing")



"""Tests for HostStore persistence."""

from __future__ import annotations

from pathlib import Path

from remoteshell_mcp.host_store import HostStore


def test_host_store_upsert_list_get_remove(tmp_path: Path):
    store = HostStore(path=tmp_path / "hosts.json")

    assert store.list() == []
    assert store.get("srv1") is None

    cfg = store.upsert(
        connection_id="srv1",
        host="1.2.3.4",
        user="root",
        auth_type="password",
        credential="secret",
    )
    assert cfg.connection_id == "srv1"
    assert cfg.port == 22
    assert cfg.last_connected is None

    cfg2 = store.get("srv1")
    assert cfg2 is not None
    assert cfg2.host == "1.2.3.4"
    assert cfg2.auth_type == "password"
    assert cfg2.port == 22

    # Can set a custom SSH port.
    store.upsert(
        connection_id="srv1",
        host="1.2.3.4",
        user="root",
        port=2222,
        auth_type="password",
        credential="secret",
    )
    cfg_port = store.get("srv1")
    assert cfg_port is not None
    assert cfg_port.port == 2222

    # Updating credentials without providing a port keeps the existing saved port.
    store.upsert(
        connection_id="srv1",
        host="1.2.3.4",
        user="root",
        auth_type="password",
        credential="secret2",
    )
    cfg_keep = store.get("srv1")
    assert cfg_keep is not None
    assert cfg_keep.port == 2222

    listed = store.list()
    assert [c.connection_id for c in listed] == ["srv1"]

    store.touch_last_connected("srv1", timestamp="2025-01-01T00:00:00+00:00")
    cfg3 = store.get("srv1")
    assert cfg3 is not None
    assert cfg3.last_connected == "2025-01-01T00:00:00+00:00"

    assert store.remove("srv1") is True
    assert store.remove("srv1") is False
    assert store.list() == []



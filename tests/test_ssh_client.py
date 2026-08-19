"""Tests for RemoteSSHClient session/channel handling without real SSH."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from remoteshell_mcp import ssh_client
from remoteshell_mcp.ssh_client import RemoteSSHClient, SSHCommandError


def _make_fake_exec(open_channels: list):
    """Build a fake exec_command that tracks open channels like a transport."""
    from paramiko.ssh_exception import SSHException

    max_sessions = 2  # mimic a small sshd MaxSessions limit

    def fake_exec_command(self, command, timeout=None, environment=None):
        if len(open_channels) >= max_sessions:
            raise SSHException("ChannelException: Administratively prohibited")
        chan = MagicMock()
        chan.closed = False

        def close():
            chan.closed = True
            if chan in open_channels:
                open_channels.remove(chan)

        chan.close.side_effect = close
        stdin = MagicMock()
        stdout = MagicMock()
        stdout.read.return_value = b"ok"
        stdout.channel = chan
        stderr = MagicMock()
        stderr.read.return_value = b""
        chan.recv_exit_status.return_value = 0
        open_channels.append(chan)
        return stdin, stdout, stderr

    return fake_exec_command


@pytest.fixture
def client():
    c = RemoteSSHClient(host="h", user="u", password="p")
    c._client = MagicMock()
    c._client.exec_command = MagicMock(
        wraps=_make_fake_exec(open_channels=[]).__get__(c._client)
    )
    # Pretend the connection is healthy so ensure_connected() is a no-op.
    with patch.object(RemoteSSHClient, "is_connected", return_value=True):
        yield c


def test_execute_command_closes_channel(client: RemoteSSHClient):
    open_channels = []

    def fake_exec(command, timeout=None, environment=None):
        chan = MagicMock()
        stdout = MagicMock()
        stdout.read.return_value = b"ok"
        stdout.channel = chan
        stderr = MagicMock()
        stderr.read.return_value = b""
        chan.recv_exit_status.return_value = 0
        open_channels.append(chan)
        return MagicMock(), stdout, stderr

    client._client.exec_command.side_effect = fake_exec

    for _ in range(10):
        result = client.execute_command("echo hi")
        assert result["success"] is True
        # Channel must be closed after each execution.
        assert open_channels[-1].close.called

    assert len(open_channels) == 10


def test_many_commands_do_not_exhaust_sessions(client: RemoteSSHClient):
    """Simulate sshd MaxSessions=2: unclosed channels would fail run 3+."""
    open_channels: list = []
    client._client.exec_command.side_effect = _make_fake_exec(open_channels).__get__(
        client._client
    )

    for _ in range(20):
        result = client.execute_command("echo hi")
        assert result["exit_code"] == 0

    assert open_channels == []


def test_connect_enables_keepalive():
    with patch.object(ssh_client.SSHClient, "connect"):
        with patch.object(
            ssh_client.SSHClient, "get_transport", return_value=MagicMock()
        ) as gt:
            c = RemoteSSHClient(host="h", user="u", password="p", keepalive_interval=15)
            c.connect()
            gt.assert_called_once()
            transport = gt.return_value
            transport.set_keepalive.assert_called_once_with(15)


def test_exec_retry_reconnects_on_ssh_exception(client: RemoteSSHClient):
    """A broken session open triggers one reconnect and a safe retry."""
    from paramiko.ssh_exception import SSHException

    open_channels: list = []
    good = _make_fake_exec(open_channels).__get__(client._client)
    calls = {"n": 0}

    def flaky(command, timeout=None, environment=None):
        calls["n"] += 1
        if calls["n"] == 1:
            raise SSHException("Socket is closed")
        return good(command, timeout=timeout)

    client._client.exec_command.side_effect = flaky

    with patch.object(RemoteSSHClient, "disconnect") as disconnect:
        with patch.object(RemoteSSHClient, "connect") as connect:
            result = client.execute_command("echo hi")

    assert result["success"] is True
    assert calls["n"] == 2
    disconnect.assert_called_once()
    connect.assert_called_once()


def test_exec_retry_gives_up_after_second_failure(client: RemoteSSHClient):
    from paramiko.ssh_exception import SSHException

    def always_fail(command, timeout=None, environment=None):
        raise SSHException("boom")

    client._client.exec_command.side_effect = always_fail

    with patch.object(RemoteSSHClient, "disconnect"):
        with patch.object(RemoteSSHClient, "connect"):
            with pytest.raises(SSHCommandError):
                client.execute_command("echo hi")

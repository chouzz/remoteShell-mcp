"""FastMCP server for RemoteShell operations."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Optional

from fastmcp import FastMCP

from .connection_manager import ConnectionManager
from .host_store import HostStore, default_hosts_path
from .ssh_client import SSHCommandError, SSHConnectionError, SSHFileTransferError


mcp = FastMCP("RemoteShell MCP")

_connection_manager: Optional[ConnectionManager] = None


def _manager() -> ConnectionManager:
    if _connection_manager is None:
        raise RuntimeError("Connection manager not initialized")
    return _connection_manager


def _error(
    *,
    code: str,
    message: str,
    connection_id: Optional[str] = None,
    details: Optional[Dict[str, Any]] = None,
    hint: Optional[str] = None,
) -> Dict[str, Any]:
    payload: Dict[str, Any] = {"success": False, "error": {"code": code, "message": f"{message} ({code})"}}
    if connection_id:
        payload["connection_id"] = connection_id
    if details:
        payload["error"]["details"] = details
    if hint:
        payload["error"]["hint"] = hint
    return payload


def _classify_error(exc: Exception) -> Dict[str, str]:
    msg = str(exc)
    lowered = msg.lower()
    if isinstance(exc, ValueError):
        if "not found" in lowered:
            return {"code": "server_not_found", "message": msg}
        return {"code": "invalid_argument", "message": msg}
    if isinstance(exc, SSHConnectionError):
        if "authentication failed" in lowered or "auth" in lowered:
            return {"code": "auth_failed", "message": f"Connection failed. {msg}"}
        if "private key" in lowered and "not found" in lowered:
            return {"code": "private_key_not_found", "message": f"Connection failed. {msg}"}
        return {"code": "connection_failed", "message": f"Connection failed. {msg}"}
    if isinstance(exc, SSHCommandError):
        return {"code": "command_failed", "message": msg}
    if isinstance(exc, SSHFileTransferError):
        if "remote file not found" in lowered:
            return {"code": "remote_not_found", "message": msg}
        if "local file not found" in lowered or "path is not a file" in lowered:
            return {"code": "local_not_found", "message": msg}
        return {"code": "transfer_failed", "message": msg}
    return {"code": "unknown_error", "message": msg}


def _default_download_path(connection_id: str, remote_path: str) -> str:
    base = Path.home() / ".config" / "remoteshell" / "downloads" / connection_id
    name = Path(remote_path).name or "download.bin"
    return str(base / name)


def _default_upload_path(remote_path: str) -> str:
    base = Path.home() / ".config" / "remoteshell" / "uploads"
    name = Path(remote_path.rstrip("/")).name or "upload.bin"
    return str(base / name)


@mcp.tool(
    description=(
        "Purpose: List all servers saved locally by this MCP server (persistent inventory).\n"
        "When to use: When the user asks to connect to a server, manage machines, or did not specify a connection_id.\n"
        "When NOT to use: Not needed if you already know the correct connection_id.\n"
        "Example: \"Show me which servers I have.\""
    )
)
def list_servers() -> Dict[str, Any]:
    manager = _manager()
    servers = manager.list_servers()
    return {
        "success": True,
        "hosts_file": str(default_hosts_path()),
        "servers": servers,
        "count": len(servers),
    }


@mcp.tool(
    description=(
        "Purpose: Persist (create or update) a server connection profile in the local host store.\n"
        "When to use: When the user provides new SSH details, or after an auth_failed error to update credentials.\n"
        "When NOT to use: Do not ask for credentials again if they are already saved and still valid.\n"
        "Example: save_server(connection_id=\"srv1\", host=\"1.2.3.4\", user=\"root\", auth_type=\"password\", credential=\"<password>\")"
    )
)
def save_server(connection_id: str, host: str, user: str, auth_type: str, credential: str) -> Dict[str, Any]:
    manager = _manager()
    try:
        cfg = manager.host_store.upsert(
            connection_id=connection_id,
            host=host,
            user=user,
            auth_type=auth_type,  # type: ignore[arg-type]
            credential=credential,
        )
        # Force reconnect on next use to apply updated credentials.
        manager.close_connection(connection_id)
        return {
            "success": True,
            "hosts_file": str(manager.host_store.path),
            "server": {
                "connection_id": cfg.connection_id,
                "host": cfg.host,
                "user": cfg.user,
                "port": cfg.port,
                "auth_type": cfg.auth_type,
                "last_connected": cfg.last_connected,
            },
            "message": f"Saved server '{connection_id}'.",
        }
    except Exception as e:
        info = _classify_error(e)
        hint = None
        if info["code"] == "auth_failed":
            hint = "Update the credential via save_server() and try again."
        return _error(code=info["code"], message=info["message"], connection_id=connection_id, hint=hint)


@mcp.tool(
    description=(
        "Purpose: Permanently delete a saved server profile from the local host store.\n"
        "When to use: Only when the user explicitly asks to forget/remove a server.\n"
        "When NOT to use: Do not remove servers just because a connection failed.\n"
        "Example: remove_server(connection_id=\"srv1\")"
    )
)
def remove_server(connection_id: str) -> Dict[str, Any]:
    manager = _manager()
    removed = manager.host_store.remove(connection_id)
    manager.close_connection(connection_id)
    if not removed:
        return _error(code="server_not_found", message=f"Server '{connection_id}' not found.", connection_id=connection_id)
    return {"success": True, "connection_id": connection_id, "message": f"Removed server '{connection_id}'."}


@mcp.tool(
    description=(
        "Purpose: Execute a non-interactive shell command on a remote server and return stdout/stderr/exit_code.\n"
        "When to use: Status checks (df, ls), file ops (cp, mv), and scripts that do not require live interaction.\n"
        "When NOT to use: Do not run interactive tools (vim, htop, top) or commands that require manual prompts.\n"
        "Example: execute_command(connection_id=\"srv1\", command=\"df -h\")"
    )
)
def execute_command(connection_id: str, command: str) -> Dict[str, Any]:
    manager = _manager()

    interactive_markers = [" vim", " nano", " htop", " top", " less", " more"]
    normalized = f" {command.strip()} "
    if any(m in normalized for m in interactive_markers):
        return _error(
            code="interactive_not_allowed",
            message="This tool only supports non-interactive commands. Use a non-interactive alternative.",
            connection_id=connection_id,
        )

    try:
        client = manager.get_or_create_connection(connection_id)
        result = client.execute_command(command=command)
        if client.is_connected():
            manager.host_store.touch_last_connected(connection_id)
        return {
            "success": bool(result.get("success")),
            "connection_id": connection_id,
            "command": command,
            "stdout": result.get("stdout", ""),
            "stderr": result.get("stderr", ""),
            "exit_code": result.get("exit_code"),
        }
    except Exception as e:
        info = _classify_error(e)
        hint = None
        if info["code"] == "auth_failed":
            hint = "Credential seems invalid. Ask the user for the updated password/private key, then call save_server()."
        return _error(code=info["code"], message=info["message"], connection_id=connection_id, details={"command": command}, hint=hint)


@mcp.tool(
    description=(
        "Purpose: Upload a local file (on the machine running this MCP server) to a remote server via SFTP.\n"
        "When to use: Deploy configs, scripts, or artifacts to the remote.\n"
        "When NOT to use: Do not upload huge files blindly; verify size/permissions first.\n"
        "Example: upload_file(connection_id=\"srv1\", local_path=\"./config.yaml\", remote_path=\"/etc/app/\")"
    )
)
def upload_file(connection_id: str, local_path: Optional[str] = None, *, remote_path: str) -> Dict[str, Any]:
    manager = _manager()
    chosen_local_path = local_path or _default_upload_path(remote_path)
    try:
        client = manager.get_or_create_connection(connection_id)
        result = client.upload_file(local_path=chosen_local_path, remote_path=remote_path)
        if client.is_connected():
            manager.host_store.touch_last_connected(connection_id)
        return {
            "success": bool(result.get("success")),
            "connection_id": connection_id,
            "local_path": result.get("local_path", chosen_local_path),
            "remote_path": result.get("remote_path", remote_path),
            "size": result.get("size"),
        }
    except Exception as e:
        info = _classify_error(e)
        return _error(
            code=info["code"],
            message=info["message"],
            connection_id=connection_id,
            details={"local_path": chosen_local_path, "remote_path": remote_path},
        )


@mcp.tool(
    description=(
        "Purpose: Download a remote file to a local path (on the machine running this MCP server) via SFTP.\n"
        "When to use: Fetch logs, reports, or backups from the remote.\n"
        "When NOT to use: Avoid very large downloads (>100MB) unless you verified size first.\n"
        "Example: download_file(connection_id=\"srv1\", remote_path=\"/var/log/syslog\", local_path=\"./logs/\")"
    )
)
def download_file(connection_id: str, remote_path: str, local_path: Optional[str] = None) -> Dict[str, Any]:
    manager = _manager()
    chosen_local_path = local_path or _default_download_path(connection_id, remote_path)
    try:
        client = manager.get_or_create_connection(connection_id)
        result = client.download_file(remote_path=remote_path, local_path=chosen_local_path)
        if client.is_connected():
            manager.host_store.touch_last_connected(connection_id)
        return {
            "success": bool(result.get("success")),
            "connection_id": connection_id,
            "remote_path": result.get("remote_path", remote_path),
            "local_path": result.get("local_path", chosen_local_path),
            "size": result.get("size"),
        }
    except Exception as e:
        info = _classify_error(e)
        return _error(
            code=info["code"],
            message=info["message"],
            connection_id=connection_id,
            details={"remote_path": remote_path, "local_path": chosen_local_path},
        )


def main() -> None:
    """Main entry point for the MCP server."""
    global _connection_manager

    host_store = HostStore()
    _connection_manager = ConnectionManager(host_store)
    mcp.run()


if __name__ == "__main__":
    main()


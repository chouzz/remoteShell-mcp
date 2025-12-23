## RemoteShell MCP

RemoteShell is a [Model Context Protocol (MCP)](https://modelcontextprotocol.io/) server that lets an LLM:

- Save SSH server profiles once (so the user doesn’t retype credentials)
- Execute **non-interactive** shell commands remotely
- Upload/download files via SFTP

This server is built with [FastMCP](https://gofastmcp.com/) and Paramiko.

## Installation


For **Claude Code** users:
```bash
claude mcp add remoteshell --scope user -- uvx remoteshell-mcp
```

Add this to your MCP client config:

```json
{
  "mcpServers": {
    "remoteshell": {
      "command": "uvx",
      "args": ["remoteshell-mcp"]
    }
  }
}
```
## Usage


## Persistent storage

RemoteShell persists servers to:

- `~/.config/remoteshell/hosts.json`

The LLM is expected to manage this file by calling `save_server` / `remove_server`.
You can also edit it manually.

Example `hosts.json`:

```json
{
  "version": 1,
  "servers": {
    "srv1": {
      "host": "1.2.3.4",
      "user": "root",
      "port": 22,
      "auth_type": "password",
      "password": "your_password_here",
      "last_connected": null
    },
    "srv2": {
      "host": "example.com",
      "user": "ubuntu",
      "port": 22,
      "auth_type": "private_key",
      "private_key": "~/.ssh/id_rsa",
      "last_connected": "2025-01-01T00:00:00+00:00"
    }
  }
}
```

On POSIX systems you should protect the file:

```bash
chmod 600 ~/.config/remoteshell/hosts.json
```

## Usage

You can configure servers either through your LLM (Claude/Cursor) by asking it to call `save_server`, or edit `~/.config/remoteshell/hosts.json` directly.

## Tools

RemoteShell exposes exactly these tools:

### `list_servers()`

- **Purpose**: List saved servers, including cached online status and `last_connected`.
- **When to use**: When the user says “connect server”, “show machines”, or did not specify a `connection_id`.
- **Example**: “Show me which servers I have.”

### `save_server(connection_id, host, user, auth_type, credential)`

- **Purpose**: Create/update a saved server profile.
- **auth_type**: `password` or `private_key`
- **credential**:
  - For `password`: the password string
  - For `private_key`: either a private key path (e.g. `~/.ssh/id_rsa`) or PEM key text
- **When to use**: New server info, or after `auth_failed` to update credentials.

### `remove_server(connection_id)`

- **Purpose**: Permanently delete a saved server profile.
- **When to use**: Only when the user explicitly asks to remove/forget a server.

### `execute_command(connection_id, command)`

- **Purpose**: Execute a **non-interactive** command remotely and return `stdout`, `stderr`, `exit_code`.
- **When NOT to use**: Interactive programs (vim/htop/top) or commands requiring manual `[Y/n]` prompts (unless you add flags like `-y`).
- **Example**: `execute_command(connection_id="srv1", command="df -h")`

### `upload_file(connection_id, local_path, remote_path)`

- **Purpose**: Upload a local file (local to the machine running this MCP server) to the remote.
- **Note**: If `remote_path` is a directory, the local filename is preserved.
- **Auto local_path**: If `local_path` is omitted, the server picks a default path and returns it in the response/error.

### `download_file(connection_id, remote_path, local_path)`

- **Purpose**: Download a remote file to a local path (local to the machine running this MCP server).
- **Auto local_path**: If `local_path` is omitted, the server defaults to `~/.config/remoteshell/downloads/<connection_id>/<basename>`.

## Development

```bash
uv run pytest
```


# 🔗 RemoteShell MCP

A [Model Context Protocol (MCP)](https://modelcontextprotocol.io/) server that enables LLMs to securely manage and execute commands on remote SSH servers.

## ✨ Features

- 🔐 **Secure credential management** - Save SSH server profiles once, no need to retype credentials
- 💻 **Remote command execution** - Execute non-interactive shell commands remotely
- 📁 **File operations** - Upload/download files via SFTP
- 🤖 **LLM-powered** - Built with [FastMCP](https://gofastmcp.com/) and Paramiko

## 🚀 Installation

### For Claude Code users
```bash
claude mcp add remoteshell --scope user -- uvx remoteshell-mcp
```

### For other MCP clients
Add this to your MCP client configuration:

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
## 📖 Usage

Getting started is easy! You can either:

1. **🤖 Let the LLM configure for you** - Simply tell the LLM your host, username, password, etc., and ask it to set up the server configuration
2. **⚙️ Manual configuration** - Directly edit the configuration file at `~/.config/remoteshell/hosts.json`


## 💾 Configuration & Storage

RemoteShell securely stores your server configurations in:

```
~/.config/remoteshell/hosts.json
```

### 🔧 Configuration Management

- **LLM-managed**: The LLM automatically manages this file using `save_server` and `remove_server` tools
- **Manual editing**: You can also directly edit the JSON file for advanced configurations

### 📋 Example Configuration

```json
{
  "version": 1,
  "servers": {
    "production-server": {
      "host": "1.2.3.4",
      "user": "root",
      "port": 22,
      "auth_type": "password",
      "password": "your_secure_password",
      "last_connected": null
    },
    "staging-server": {
      "host": "staging.example.com",
      "user": "ubuntu",
      "port": 22,
      "auth_type": "private_key",
      "private_key": "~/.ssh/id_rsa",
      "last_connected": "2025-01-01T00:00:00+00:00"
    }
  }
}
```

### 🔒 Security Note

On POSIX systems, protect your configuration file:

```bash
chmod 600 ~/.config/remoteshell/hosts.json
```

## 🛠️ Available Tools

RemoteShell provides the following MCP tools for remote server management:

### 📋 `list_servers()`

**Purpose**: Display all saved server profiles with their connection status and last activity.

**When to use**:
- User asks to "connect to server" or "show machines"
- No specific `connection_id` is provided
- Need to see available servers

**Example**: *"Show me which servers I have configured"* → Returns list of all saved servers with online status

### 💾 `save_server(connection_id, host, user, auth_type, credential, port)`

**Purpose**: Create or update a server profile with authentication credentials.

**Parameters**:
- `connection_id`: Unique identifier for the server (e.g., "production", "staging")
- `host`: Server hostname or IP address
- `user`: SSH username
- `auth_type`: `"password"` or `"private_key"`
- `credential`:
  - For `password`: Plain text password string
  - For `private_key`: File path (e.g., `~/.ssh/id_rsa`) or PEM key content
- `port`: SSH port (optional; defaults to 22 and keeps the existing saved port if omitted)

**When to use**:
- Adding a new server configuration
- Updating credentials after authentication failure
- Changing server connection details

### 🗑️ `remove_server(connection_id)`

**Purpose**: Permanently delete a server profile from storage.

**When to use**:
- User explicitly requests to remove or forget a server
- Server is no longer accessible or needed

⚠️ **Warning**: This action cannot be undone

### ⚡ `execute_command(connection_id, command)`

**Purpose**: Execute non-interactive shell commands remotely and return results.

**Returns**: `stdout`, `stderr`, and `exit_code`

**When to use**:
- Running system commands, scripts, or utilities
- Checking server status, disk usage, process lists
- File operations, package management, etc.

**When NOT to use**:
- Interactive programs (vim, htop, top)
- Commands requiring manual input (`[Y/n]` prompts) - unless using flags like `-y`

**Example**: `execute_command(connection_id="production", command="df -h")`

### 📤 `upload_file(connection_id, local_path, remote_path)`

**Purpose**: Upload files from your local machine to a remote server via SFTP.

**Parameters**:
- `local_path`: Path to the file on your local machine
- `remote_path`: Destination path on the remote server

**Notes**:
- If `remote_path` is a directory, the original filename is preserved
- If `local_path` is omitted, server selects a default and returns it in response

### 📥 `download_file(connection_id, remote_path, local_path)`

**Purpose**: Download files from a remote server to your local machine via SFTP.

**Parameters**:
- `remote_path`: Path to the file on the remote server
- `local_path`: Destination path on your local machine

**Notes**:
- If `local_path` is omitted, defaults to: `~/.config/remoteshell/downloads/<connection_id>/<basename>`

## 🧪 Development

### Local Development Setup

For local development, use this MCP configuration:

```json
{
  "mcpServers": {
    "remoteshell": {
      "command": "uv",
      "args": ["--directory", "/absolute/path/to/remoteShell-mcp", "run", "remoteshell-mcp"]
    }
  }
}
```

### Running Tests

```bash
uv run pytest
```


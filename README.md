# Remote Shell MCP Server

[![PyPI version](https://badge.fury.io/py/remoteshell-mcp.svg)](https://badge.fury.io/py/remoteshell-mcp)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Tests](https://github.com/chouzz/remoteShell-mcp/workflows/Run%20Tests/badge.svg)](https://github.com/chouzz/remoteShell-mcp/actions)

A Model Context Protocol (MCP) server that enables AI models to manage SSH connections and execute commands on remote machines without repeatedly entering credentials. Built with FastMCP and Paramiko for cross-platform compatibility.

## Features

- 🔐 **Multiple Authentication Methods**: Support both password and SSH key authentication
- 🔄 **Persistent Connections**: Create and maintain SSH connections across multiple operations
- 📁 **File Transfer**: Upload and download files between local and remote machines
- ⚙️ **Flexible Configuration**: Three ways to configure connections (global config, server args, or dynamic)
- 🌐 **Multi-Connection Support**: Manage multiple remote hosts simultaneously
- 🛠️ **Simple MCP Tools**: Easy-to-use tools for command execution and file operations

## Installation

### Option 1: Install from PyPI (Recommended)

```bash
# Install with pip
pip install remoteshell-mcp

# Or install with uv
uv pip install remoteshell-mcp
```

### Option 2: Install from Source

#### Prerequisites

- Python 3.11 or higher
- [uv](https://github.com/astral-sh/uv) package manager

#### Steps

```bash
# Clone the repository
git clone https://github.com/chouzz/remoteShell-mcp.git
cd remoteShell-mcp

# Install dependencies
uv sync

# The server is now ready to use
```

## Configuration

There are three ways to configure SSH connections:

### 1. Global Configuration File (Recommended for Personal Use)

Create a configuration file at `~/.remoteShell/config.json`:

```json
{
  "connections": [
    {
      "id": "prod-server",
      "host": "192.168.1.100",
      "port": 22,
      "user": "admin",
      "auth_type": "password",
      "password": "your_password"
    },
    {
      "id": "dev-server",
      "host": "192.168.1.101",
      "port": 22,
      "user": "developer",
      "auth_type": "key",
      "key_path": "~/.ssh/id_rsa"
    }
  ]
}
```

**Security Note**: Ensure this file has proper permissions:
```bash
chmod 600 ~/.remoteShell/config.json
```

### 2. MCP Client Configuration (Recommended for Claude Code/Cursor)

Configure connections directly in your MCP client settings (see below for specific examples).

### 3. Dynamic Creation

Create connections on-the-fly using the `create_connection` tool during a conversation with your AI assistant.

## Client Setup

### Claude Code Configuration

Add the following to your Claude Code MCP settings file (usually located at `~/Library/Application Support/Claude/claude_desktop_config.json` on macOS):

```json
{
  "mcpServers": {
    "remoteshell": {
      "command": "uv",
      "args": [
        "--directory",
        "/absolute/path/to/remoteShell-mcp",
        "run",
        "remoteshell-mcp"
      ]
    }
  }
}
```

#### With Pre-configured Connections:

```json
{
  "mcpServers": {
    "remoteshell": {
      "command": "uv",
      "args": [
        "--directory",
        "/absolute/path/to/remoteShell-mcp",
        "run",
        "remoteshell-mcp",
        "--connections",
        "[{\"id\":\"server1\",\"host\":\"192.168.1.100\",\"user\":\"admin\",\"auth_type\":\"password\",\"password\":\"secret\"}]"
      ]
    }
  }
}
```

Or reference a configuration file:

```json
{
  "mcpServers": {
    "remoteshell": {
      "command": "uv",
      "args": [
        "--directory",
        "/absolute/path/to/remoteShell-mcp",
        "run",
        "remoteshell-mcp",
        "--connections",
        "/path/to/your/connections.json"
      ]
    }
  }
}
```

### Cursor Configuration

Add the following to your Cursor settings (Settings → Features → MCP):

```json
{
  "mcpServers": {
    "remoteshell": {
      "command": "uv",
      "args": [
        "--directory",
        "/absolute/path/to/remoteShell-mcp",
        "run",
        "remoteshell-mcp"
      ]
    }
  }
}
```

#### With Pre-configured Connections:

```json
{
  "mcpServers": {
    "remoteshell": {
      "command": "uv",
      "args": [
        "--directory",
        "/absolute/path/to/remoteShell-mcp",
        "run",
        "remoteshell-mcp",
        "--connections",
        "/path/to/your/connections.json"
      ]
    }
  }
}
```

**Note**: Replace `/absolute/path/to/remoteShell-mcp` with the actual absolute path to this repository on your system.

## Available Tools

### 1. `create_connection`

Create a new SSH connection to a remote host.

**Parameters:**
- `host` (required): Remote host address (IP or domain)
- `user` (required): Username for authentication
- `port` (optional): SSH port (default: 22)
- `password` (optional): Password for authentication
- `key_path` (optional): Path to SSH private key file
- `connection_id` (optional): Custom connection ID (auto-generated if not provided)

**Example Usage:**
```
Create a connection to 192.168.1.100 with username admin and password secret123
```

### 2. `execute_command`

Execute a command on a remote host.

**Parameters:**
- `connection_id` (required): ID of the connection to use
- `command` (required): Command to execute
- `timeout` (optional): Command timeout in seconds
- `working_dir` (optional): Working directory for command execution

**Example Usage:**
```
Execute "ls -la /home" on prod-server
```

### 3. `upload_file`

Upload a file from local machine to remote host.

**Parameters:**
- `connection_id` (required): ID of the connection to use
- `local_path` (required): Path to local file
- `remote_path` (required): Destination path on remote host

**Example Usage:**
```
Upload /tmp/config.txt to /etc/app/config.txt on prod-server
```

### 4. `download_file`

Download a file from remote host to local machine.

**Parameters:**
- `connection_id` (required): ID of the connection to use
- `remote_path` (required): Path to file on remote host
- `local_path` (required): Destination path on local machine

**Example Usage:**
```
Download /var/log/app.log from prod-server to /tmp/app.log
```

### 5. `list_connections`

List all available connections (both active and pre-configured).

**Example Usage:**
```
Show me all available connections
```

### 6. `close_connection`

Close an active SSH connection.

**Parameters:**
- `connection_id` (required): ID of the connection to close

**Example Usage:**
```
Close the connection to prod-server
```

## Usage Examples

### Basic Workflow

1. **List available connections:**
   ```
   Show me all configured connections
   ```

2. **Execute a command:**
   ```
   Run "df -h" on prod-server
   ```

3. **Create a new connection dynamically:**
   ```
   Connect to 192.168.1.200 with username ubuntu using SSH key at ~/.ssh/mykey.pem, call it web-server
   ```

4. **Upload a file:**
   ```
   Upload my local file /tmp/data.csv to /home/user/data.csv on web-server
   ```

5. **Download a file:**
   ```
   Download /var/log/nginx/access.log from web-server to ~/Downloads/access.log
   ```

### Advanced Usage

**Execute commands in a specific directory:**
```
Run "npm install" on dev-server in the /var/www/myapp directory
```

**Check system resources on multiple servers:**
```
Check disk space on prod-server and dev-server
```

**Batch file operations:**
```
Upload all .conf files from /etc/local to /etc/remote on backup-server
```

## Security Considerations

1. **Credential Storage**: 
   - Store passwords and keys securely
   - Use file permissions to protect config files (chmod 600)
   - Consider using SSH keys instead of passwords when possible

2. **SSH Key Authentication**:
   - More secure than password authentication
   - Keys can be password-protected for additional security
   - Use different keys for different hosts when possible

3. **Connection Timeouts**:
   - Set appropriate timeouts to prevent hanging connections
   - Connections automatically reconnect if they drop

4. **Global Config File**:
   - Located at `~/.remoteShell/config.json`
   - Should have restrictive permissions (600)
   - Consider encrypting sensitive data at rest

## Troubleshooting

### Connection Issues

**Problem**: "Authentication failed"
- **Solution**: Verify username and password/key path are correct
- **Solution**: Ensure SSH key has proper permissions (chmod 600)

**Problem**: "Connection timed out"
- **Solution**: Check if host is reachable (ping)
- **Solution**: Verify firewall rules allow SSH connections
- **Solution**: Confirm SSH service is running on remote host

**Problem**: "SSH key file not found"
- **Solution**: Use absolute path or expand ~ properly
- **Solution**: Verify file exists and is readable

### File Transfer Issues

**Problem**: "Permission denied" during upload
- **Solution**: Check write permissions on remote directory
- **Solution**: Ensure remote user has necessary permissions

**Problem**: "No such file or directory" during download
- **Solution**: Verify remote file path is correct
- **Solution**: Check if file exists on remote host

## Development

### Running Tests

```bash
uv run pytest
```

### Project Structure

```
remoteShell-mcp/
├── src/
│   └── remoteshell_mcp/
│       ├── __init__.py
│       ├── server.py              # FastMCP server with tools
│       ├── connection_manager.py  # SSH connection management
│       ├── ssh_client.py          # Paramiko wrapper
│       └── config_loader.py       # Configuration handling
├── config.example.json            # Example configuration
├── pyproject.toml                 # Project dependencies
└── README.md                      # This file
```

## License

MIT License - See LICENSE file for details

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## Support

For issues, questions, or contributions, please open an issue on the GitHub repository.


# Quick Start Guide

## Installation

```bash
# Clone and install
git clone https://github.com/chouzz/remoteShell-mcp.git
cd remoteShell-mcp
uv sync
```

## Configuration

### Option 1: Global Config (Easiest)

Create `~/.remoteShell/config.json`:

```json
{
  "connections": [
    {
      "id": "my-server",
      "host": "192.168.1.100",
      "user": "admin",
      "auth_type": "password",
      "password": "your_password"
    }
  ]
}
```

### Option 2: Claude Code Config

Edit `~/Library/Application Support/Claude/claude_desktop_config.json`:

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

### Option 3: Cursor Config

In Cursor settings (Settings → Features → MCP), add:

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

## Common Commands

### List Connections
```
Show me all available connections
```

### Create Connection
```
Create a connection to 192.168.1.100 with username admin and password secret
```

### Execute Command
```
Run "ls -la" on my-server
```

### Upload File
```
Upload /tmp/file.txt to /home/user/file.txt on my-server
```

### Download File
```
Download /var/log/app.log from my-server to ~/Downloads/app.log
```

### Close Connection
```
Close the connection to my-server
```

## Security Tips

1. **Use SSH Keys**: More secure than passwords
   ```json
   {
     "id": "secure-server",
     "host": "example.com",
     "user": "ubuntu",
     "auth_type": "key",
     "key_path": "~/.ssh/id_rsa"
   }
   ```

2. **Protect Config File**:
   ```bash
   chmod 600 ~/.remoteShell/config.json
   ```

3. **Use Strong Passwords**: If using password authentication

## Troubleshooting

### Connection Failed
- Check host is reachable: `ping <host>`
- Verify SSH port is open: `telnet <host> 22`
- Confirm credentials are correct

### Permission Denied
- Check file permissions on SSH key: `chmod 600 ~/.ssh/id_rsa`
- Verify user has necessary permissions on remote system

### File Transfer Failed
- Ensure destination directory exists
- Check disk space on target system
- Verify file paths are correct

## Examples

### System Monitoring
```
Check disk space on my-server
Check memory usage on my-server
Show running processes on my-server
```

### File Management
```
List files in /var/log on my-server
Download all log files from /var/log to ~/logs on my-server
Upload config.json to /etc/app/ on my-server
```

### Application Management
```
Restart nginx on my-server
Check nginx status on my-server
View nginx error logs on my-server
```


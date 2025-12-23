"""FastMCP server for remote shell operations."""

from typing import Optional, Dict, Any
import sys
from fastmcp import FastMCP

from .config_loader import ConfigLoader, ConnectionConfig
from .connection_manager import ConnectionManager
from .ssh_client import SSHConnectionError, SSHCommandError, SSHFileTransferError
from .command_validator import CommandValidator, DangerousCommandError


# Initialize FastMCP server
mcp = FastMCP("Remote Shell MCP")

# Global connection manager (will be initialized in main)
_connection_manager: Optional[ConnectionManager] = None


def get_connection_manager() -> ConnectionManager:
    """Get the global connection manager instance."""
    if _connection_manager is None:
        raise RuntimeError("Connection manager not initialized")
    return _connection_manager


@mcp.tool()
def create_connection(
    host: str,
    user: str,
    port: int = 22,
    password: Optional[str] = None,
    key_path: Optional[str] = None,
    connection_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Create a new SSH connection to a remote host.
    
    Args:
        host: Remote host address (IP or domain name)
        user: Username for authentication
        port: SSH port (default: 22)
        password: Password for authentication (provide either password or key_path)
        key_path: Path to SSH private key file (provide either password or key_path)
        connection_id: Custom connection ID (optional, auto-generated if not provided)
    
    Returns:
        Dictionary with connection details including the connection_id
    
    Examples:
        - create_connection(host="192.168.1.100", user="admin", password="secret123")
        - create_connection(host="server.example.com", user="ubuntu", key_path="~/.ssh/id_rsa", connection_id="my-server")
    """
    manager = get_connection_manager()
    
    try:
        conn_id = manager.create_connection(
            host=host,
            user=user,
            port=port,
            password=password,
            key_path=key_path,
            connection_id=connection_id,
            auto_connect=True
        )
        
        return {
            "success": True,
            "connection_id": conn_id,
            "host": host,
            "user": user,
            "port": port,
            "message": f"Successfully connected to {user}@{host}:{port}"
        }
    
    except (ValueError, SSHConnectionError) as e:
        return {
            "success": False,
            "error": str(e),
            "message": f"Failed to create connection: {e}"
        }


@mcp.tool()
def execute_command(
    connection_id: str,
    command: str,
    timeout: Optional[int] = None,
    working_dir: Optional[str] = None
) -> Dict[str, Any]:
    """
    Execute a command on a remote host.
    
    Args:
        connection_id: ID of the connection to use (can be pre-configured or dynamically created)
        command: Command to execute on the remote host
        timeout: Command timeout in seconds (optional)
        working_dir: Working directory for command execution (optional)
    
    Returns:
        Dictionary with command output (stdout, stderr, exit_code, success)
    
    Examples:
        - execute_command(connection_id="prod-server", command="ls -la /home")
        - execute_command(connection_id="dev-server", command="df -h", timeout=10)
        - execute_command(connection_id="web-server", command="ls", working_dir="/var/www/html")
    """
    manager = get_connection_manager()
    
    try:
        # Validate command before execution
        CommandValidator.validate(command)
        
        # Get or create connection
        client = manager.get_or_create_connection(connection_id)
        
        # Execute command
        result = client.execute_command(
            command=command,
            timeout=timeout,
            working_dir=working_dir
        )
        
        return {
            "success": result["success"],
            "connection_id": connection_id,
            "command": command,
            "stdout": result["stdout"],
            "stderr": result["stderr"],
            "exit_code": result["exit_code"]
        }
    
    except DangerousCommandError as e:
        return {
            "success": False,
            "error": str(e),
            "connection_id": connection_id,
            "command": command,
            "message": f"命令验证失败: {e}"
        }
    except (ValueError, SSHConnectionError, SSHCommandError) as e:
        return {
            "success": False,
            "error": str(e),
            "connection_id": connection_id,
            "command": command,
            "message": f"Command execution failed: {e}"
        }


@mcp.tool()
def upload_file(
    connection_id: str,
    local_path: str,
    remote_path: str
) -> Dict[str, Any]:
    """
    Upload a file from local machine to remote host.
    
    Args:
        connection_id: ID of the connection to use
        local_path: Path to local file to upload
        remote_path: Destination path on remote host
    
    Returns:
        Dictionary with upload status and file information
    
    Examples:
        - upload_file(connection_id="prod-server", local_path="/tmp/config.txt", remote_path="/etc/app/config.txt")
        - upload_file(connection_id="dev-server", local_path="~/data.csv", remote_path="/home/user/data.csv")
    """
    manager = get_connection_manager()
    
    try:
        # Get or create connection
        client = manager.get_or_create_connection(connection_id)
        
        # Upload file
        result = client.upload_file(
            local_path=local_path,
            remote_path=remote_path
        )
        
        return {
            "success": result["success"],
            "connection_id": connection_id,
            "local_path": result["local_path"],
            "remote_path": result["remote_path"],
            "size": result["size"],
            "message": f"Successfully uploaded {result['size']} bytes"
        }
    
    except (ValueError, SSHConnectionError, SSHFileTransferError) as e:
        return {
            "success": False,
            "error": str(e),
            "connection_id": connection_id,
            "local_path": local_path,
            "remote_path": remote_path,
            "message": f"File upload failed: {e}"
        }


@mcp.tool()
def download_file(
    connection_id: str,
    remote_path: str,
    local_path: str
) -> Dict[str, Any]:
    """
    Download a file from remote host to local machine.
    
    Args:
        connection_id: ID of the connection to use
        remote_path: Path to file on remote host
        local_path: Destination path on local machine
    
    Returns:
        Dictionary with download status and file information
    
    Examples:
        - download_file(connection_id="prod-server", remote_path="/var/log/app.log", local_path="/tmp/app.log")
        - download_file(connection_id="dev-server", remote_path="/home/user/report.pdf", local_path="~/Downloads/report.pdf")
    """
    manager = get_connection_manager()
    
    try:
        # Get or create connection
        client = manager.get_or_create_connection(connection_id)
        
        # Download file
        result = client.download_file(
            remote_path=remote_path,
            local_path=local_path
        )
        
        return {
            "success": result["success"],
            "connection_id": connection_id,
            "remote_path": result["remote_path"],
            "local_path": result["local_path"],
            "size": result["size"],
            "message": f"Successfully downloaded {result['size']} bytes"
        }
    
    except (ValueError, SSHConnectionError, SSHFileTransferError) as e:
        return {
            "success": False,
            "error": str(e),
            "connection_id": connection_id,
            "remote_path": remote_path,
            "local_path": local_path,
            "message": f"File download failed: {e}"
        }


@mcp.tool()
def list_connections() -> Dict[str, Any]:
    """
    List all available connections (active and pre-configured).
    
    Returns:
        Dictionary with lists of active and pre-configured connections
    
    Example:
        - list_connections()
    """
    manager = get_connection_manager()
    
    try:
        active = manager.list_active_connections()
        preconfigured = manager.list_preconfigured_connections()
        
        return {
            "success": True,
            "active_connections": active,
            "preconfigured_connections": preconfigured,
            "message": f"Found {len(active)} active and {len(preconfigured)} pre-configured connections"
        }
    
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "message": f"Failed to list connections: {e}"
        }


@mcp.tool()
def close_connection(connection_id: str) -> Dict[str, Any]:
    """
    Close an active SSH connection.
    
    Args:
        connection_id: ID of the connection to close
    
    Returns:
        Dictionary with success status
    
    Example:
        - close_connection(connection_id="prod-server")
    """
    manager = get_connection_manager()
    
    try:
        success = manager.close_connection(connection_id)
        
        if success:
            return {
                "success": True,
                "connection_id": connection_id,
                "message": f"Connection '{connection_id}' closed successfully"
            }
        else:
            return {
                "success": False,
                "connection_id": connection_id,
                "message": f"Connection '{connection_id}' not found"
            }
    
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "connection_id": connection_id,
            "message": f"Failed to close connection: {e}"
        }


def main():
    """Main entry point for the MCP server."""
    global _connection_manager
    
    # Parse server arguments (passed from MCP client configuration)
    server_args = {}
    
    # Check for --connections argument (JSON string or file path)
    if len(sys.argv) > 1:
        for i, arg in enumerate(sys.argv[1:]):
            if arg == "--connections" and i + 1 < len(sys.argv) - 1:
                import json
                connections_arg = sys.argv[i + 2]
                try:
                    # Try to parse as JSON
                    server_args["connections"] = json.loads(connections_arg)
                except json.JSONDecodeError:
                    # If not JSON, treat as file path
                    try:
                        with open(connections_arg, 'r') as f:
                            data = json.load(f)
                            server_args["connections"] = data.get("connections", [])
                    except (IOError, json.JSONDecodeError) as e:
                        print(f"Warning: Failed to load connections: {e}", file=sys.stderr)
    
    # Initialize config loader
    config_loader = ConfigLoader(server_args=server_args)
    
    # Initialize connection manager
    _connection_manager = ConnectionManager(config_loader)
    
    # Run the server
    mcp.run()


if __name__ == "__main__":
    main()


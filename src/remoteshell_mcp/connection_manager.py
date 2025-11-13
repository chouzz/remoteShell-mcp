"""Connection manager for handling multiple SSH connections."""

from typing import Dict, List, Optional, Any
import uuid
from .ssh_client import RemoteSSHClient, SSHConnectionError
from .config_loader import ConnectionConfig, ConfigLoader


class ConnectionManager:
    """Manages multiple SSH connections."""
    
    def __init__(self, config_loader: ConfigLoader):
        """
        Initialize connection manager.
        
        Args:
            config_loader: ConfigLoader instance with pre-configured connections
        """
        self.config_loader = config_loader
        self.active_connections: Dict[str, RemoteSSHClient] = {}
        self.connection_configs: Dict[str, ConnectionConfig] = {}
    
    def create_connection(
        self,
        host: str,
        user: str,
        port: int = 22,
        password: Optional[str] = None,
        key_path: Optional[str] = None,
        connection_id: Optional[str] = None,
        auto_connect: bool = True
    ) -> str:
        """
        Create a new SSH connection.
        
        Args:
            host: Remote host address
            user: Username for authentication
            port: SSH port
            password: Password for authentication (optional)
            key_path: Path to SSH private key (optional)
            connection_id: Custom connection ID (optional, auto-generated if not provided)
            auto_connect: Whether to connect immediately
        
        Returns:
            Connection ID
        
        Raises:
            ValueError: If connection with given ID already exists
            SSHConnectionError: If connection fails
        """
        # Generate connection ID if not provided
        if connection_id is None:
            connection_id = f"conn_{uuid.uuid4().hex[:8]}"
        
        # Check if connection ID already exists
        if connection_id in self.active_connections:
            raise ValueError(f"Connection with ID '{connection_id}' already exists")
        
        # Determine auth type
        if key_path:
            auth_type = "key"
        elif password:
            auth_type = "password"
        else:
            raise ValueError("Either password or key_path must be provided")
        
        # Create connection config
        config = ConnectionConfig(
            id=connection_id,
            host=host,
            user=user,
            port=port,
            auth_type=auth_type,
            password=password,
            key_path=key_path
        )
        config.validate()
        
        # Create SSH client
        client = RemoteSSHClient(
            host=host,
            user=user,
            port=port,
            password=password,
            key_path=key_path
        )
        
        # Connect if requested
        if auto_connect:
            client.connect()
        
        # Store connection
        self.active_connections[connection_id] = client
        self.connection_configs[connection_id] = config
        
        return connection_id
    
    def get_or_create_connection(self, connection_id: str) -> RemoteSSHClient:
        """
        Get an existing connection or create from pre-configured settings.
        
        Args:
            connection_id: Connection ID
        
        Returns:
            RemoteSSHClient instance
        
        Raises:
            ValueError: If connection doesn't exist and no config found
            SSHConnectionError: If connection fails
        """
        # Check if connection already exists
        if connection_id in self.active_connections:
            return self.active_connections[connection_id]
        
        # Try to get pre-configured connection
        config = self.config_loader.get_connection(connection_id)
        if config is None:
            raise ValueError(
                f"Connection '{connection_id}' not found. "
                f"Available connections: {', '.join(self.list_connection_ids())}"
            )
        
        # Create connection from config
        self.create_connection(
            host=config.host,
            user=config.user,
            port=config.port,
            password=config.password,
            key_path=config.key_path,
            connection_id=connection_id,
            auto_connect=True
        )
        
        return self.active_connections[connection_id]
    
    def get_connection(self, connection_id: str) -> Optional[RemoteSSHClient]:
        """
        Get an active connection by ID.
        
        Args:
            connection_id: Connection ID
        
        Returns:
            RemoteSSHClient instance or None if not found
        """
        return self.active_connections.get(connection_id)
    
    def close_connection(self, connection_id: str) -> bool:
        """
        Close and remove a connection.
        
        Args:
            connection_id: Connection ID
        
        Returns:
            True if connection was closed, False if not found
        """
        if connection_id in self.active_connections:
            client = self.active_connections[connection_id]
            client.disconnect()
            del self.active_connections[connection_id]
            if connection_id in self.connection_configs:
                del self.connection_configs[connection_id]
            return True
        return False
    
    def close_all_connections(self) -> None:
        """Close all active connections."""
        for connection_id in list(self.active_connections.keys()):
            self.close_connection(connection_id)
    
    def list_connection_ids(self) -> List[str]:
        """
        List all connection IDs (active and pre-configured).
        
        Returns:
            List of connection IDs
        """
        # Combine active and pre-configured connection IDs
        active_ids = set(self.active_connections.keys())
        config_ids = set(config.id for config in self.config_loader.list_connections())
        return sorted(active_ids | config_ids)
    
    def list_active_connections(self) -> List[Dict[str, Any]]:
        """
        List all active connections with their details.
        
        Returns:
            List of connection information dictionaries
        """
        connections = []
        for connection_id, client in self.active_connections.items():
            config = self.connection_configs.get(connection_id)
            info = {
                "id": connection_id,
                "host": client.host,
                "user": client.user,
                "port": client.port,
                "connected": client.is_connected(),
                "auth_type": config.auth_type if config else "unknown"
            }
            connections.append(info)
        return connections
    
    def list_preconfigured_connections(self) -> List[Dict[str, Any]]:
        """
        List all pre-configured connections (not necessarily active).
        
        Returns:
            List of connection configuration dictionaries
        """
        configs = []
        for config in self.config_loader.list_connections():
            info = {
                "id": config.id,
                "host": config.host,
                "user": config.user,
                "port": config.port,
                "auth_type": config.auth_type,
                "active": config.id in self.active_connections
            }
            configs.append(info)
        return configs
    
    def reconnect(self, connection_id: str) -> None:
        """
        Reconnect an existing connection.
        
        Args:
            connection_id: Connection ID
        
        Raises:
            ValueError: If connection doesn't exist
            SSHConnectionError: If reconnection fails
        """
        client = self.active_connections.get(connection_id)
        if client is None:
            raise ValueError(f"Connection '{connection_id}' not found")
        
        client.disconnect()
        client.connect()
    
    def ensure_connected(self, connection_id: str) -> None:
        """
        Ensure a connection is active, reconnect if necessary.
        
        Args:
            connection_id: Connection ID
        
        Raises:
            ValueError: If connection doesn't exist
            SSHConnectionError: If connection fails
        """
        client = self.get_or_create_connection(connection_id)
        client.ensure_connected()
    
    def __del__(self):
        """Cleanup all connections on deletion."""
        self.close_all_connections()


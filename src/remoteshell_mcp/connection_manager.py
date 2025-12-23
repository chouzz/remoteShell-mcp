"""Connection manager for handling multiple SSH connections."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from .host_store import HostStore, ServerConfig
from .ssh_client import RemoteSSHClient, SSHConnectionError


class ConnectionManager:
    """Manages multiple SSH connections."""
    
    def __init__(self, host_store: HostStore):
        """Initialize connection manager.

        Args:
            host_store: Persistent store for server configurations.
        """
        self.host_store = host_store
        self.active_connections: Dict[str, RemoteSSHClient] = {}
        self.connection_configs: Dict[str, ServerConfig] = {}
    
    def _connect_from_config(self, config: ServerConfig) -> RemoteSSHClient:
        """Create and connect an SSH client from a stored config."""
        client = RemoteSSHClient(
            host=config.host,
            user=config.user,
            port=config.port,
            password=config.password if config.auth_type == "password" else None,
            private_key=config.private_key if config.auth_type == "private_key" else None,
        )
        client.connect()
        # Successful connect -> persist last_connected.
        self.host_store.touch_last_connected(config.connection_id)
        return client
    
    def get_or_create_connection(self, connection_id: str) -> RemoteSSHClient:
        """
        Get an existing connection or create from persistent host settings.
        
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
        
        # Try to load persisted server config
        config = self.host_store.get(connection_id)
        if config is None:
            raise ValueError(
                f"Server '{connection_id}' not found. "
                f"Available servers: {', '.join(self.list_connection_ids())}"
            )
        
        client = self._connect_from_config(config)
        self.active_connections[connection_id] = client
        self.connection_configs[connection_id] = config
        return client
    
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
        List all server IDs (active and persisted).
        
        Returns:
            List of connection IDs
        """
        # Combine active and persisted connection IDs
        active_ids = set(self.active_connections.keys())
        persisted_ids = set(cfg.connection_id for cfg in self.host_store.list())
        return sorted(active_ids | persisted_ids)
    
    def list_servers(self) -> List[Dict[str, Any]]:
        """Return persisted servers enriched with cached online status."""
        out: List[Dict[str, Any]] = []
        for cfg in self.host_store.list():
            client = self.active_connections.get(cfg.connection_id)
            online = bool(client and client.is_connected())
            out.append(
                {
                    "connection_id": cfg.connection_id,
                    "host": cfg.host,
                    "user": cfg.user,
                    "port": cfg.port,
                    "auth_type": cfg.auth_type,
                    "online": online,
                    "last_connected": cfg.last_connected,
                }
            )
        return out
    
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
        # Successful reconnect -> persist last_connected.
        self.host_store.touch_last_connected(connection_id)
    
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
        if client.is_connected():
            self.host_store.touch_last_connected(connection_id)
    
    def __del__(self):
        """Cleanup all connections on deletion."""
        self.close_all_connections()


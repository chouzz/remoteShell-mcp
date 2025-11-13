"""Configuration loader for SSH connections."""

import json
import os
from pathlib import Path
from typing import Any, Dict, List, Optional
from dataclasses import dataclass


@dataclass
class ConnectionConfig:
    """Configuration for a single SSH connection."""
    
    id: str
    host: str
    user: str
    port: int = 22
    auth_type: str = "password"  # "password" or "key"
    password: Optional[str] = None
    key_path: Optional[str] = None
    
    def validate(self) -> None:
        """Validate the connection configuration."""
        if not self.id:
            raise ValueError("Connection ID is required")
        if not self.host:
            raise ValueError("Host is required")
        if not self.user:
            raise ValueError("User is required")
        if self.auth_type not in ["password", "key"]:
            raise ValueError("auth_type must be 'password' or 'key'")
        if self.auth_type == "password" and not self.password:
            raise ValueError("Password is required for password authentication")
        if self.auth_type == "key" and not self.key_path:
            raise ValueError("key_path is required for key authentication")
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ConnectionConfig":
        """Create a ConnectionConfig from a dictionary."""
        return cls(
            id=data.get("id", ""),
            host=data.get("host", ""),
            user=data.get("user", ""),
            port=data.get("port", 22),
            auth_type=data.get("auth_type", "password"),
            password=data.get("password"),
            key_path=data.get("key_path")
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert ConnectionConfig to dictionary."""
        result = {
            "id": self.id,
            "host": self.host,
            "user": self.user,
            "port": self.port,
            "auth_type": self.auth_type,
        }
        if self.password:
            result["password"] = self.password
        if self.key_path:
            result["key_path"] = self.key_path
        return result


class ConfigLoader:
    """Loads connection configurations from multiple sources."""
    
    GLOBAL_CONFIG_DIR = Path.home() / ".remoteShell"
    GLOBAL_CONFIG_FILE = GLOBAL_CONFIG_DIR / "config.json"
    
    def __init__(self, server_args: Optional[Dict[str, Any]] = None):
        """
        Initialize the config loader.
        
        Args:
            server_args: Optional dictionary containing server arguments,
                        can include a "connections" key with connection configs
        """
        self.server_args = server_args or {}
        self.connections: Dict[str, ConnectionConfig] = {}
        self._load_configs()
    
    def _load_configs(self) -> None:
        """Load configurations from all sources."""
        # Load from global config file first
        global_configs = self._load_global_config()
        for config in global_configs:
            self.connections[config.id] = config
        
        # Load from server args (overrides global config)
        server_configs = self._load_server_args()
        for config in server_configs:
            self.connections[config.id] = config
    
    def _load_global_config(self) -> List[ConnectionConfig]:
        """Load configurations from global config file."""
        configs = []
        
        if not self.GLOBAL_CONFIG_FILE.exists():
            return configs
        
        try:
            with open(self.GLOBAL_CONFIG_FILE, 'r') as f:
                data = json.load(f)
            
            connections_data = data.get("connections", [])
            for conn_data in connections_data:
                try:
                    config = ConnectionConfig.from_dict(conn_data)
                    config.validate()
                    configs.append(config)
                except (ValueError, KeyError) as e:
                    print(f"Warning: Invalid connection config in global file: {e}")
                    continue
        
        except (json.JSONDecodeError, IOError) as e:
            print(f"Warning: Failed to load global config file: {e}")
        
        return configs
    
    def _load_server_args(self) -> List[ConnectionConfig]:
        """Load configurations from server arguments."""
        configs = []
        
        connections_data = self.server_args.get("connections", [])
        if isinstance(connections_data, str):
            # If connections is a JSON string, parse it
            try:
                connections_data = json.loads(connections_data)
            except json.JSONDecodeError as e:
                print(f"Warning: Failed to parse connections from server args: {e}")
                return configs
        
        for conn_data in connections_data:
            try:
                config = ConnectionConfig.from_dict(conn_data)
                config.validate()
                configs.append(config)
            except (ValueError, KeyError) as e:
                print(f"Warning: Invalid connection config in server args: {e}")
                continue
        
        return configs
    
    def get_connection(self, connection_id: str) -> Optional[ConnectionConfig]:
        """Get a connection configuration by ID."""
        return self.connections.get(connection_id)
    
    def list_connections(self) -> List[ConnectionConfig]:
        """List all configured connections."""
        return list(self.connections.values())
    
    def add_connection(self, config: ConnectionConfig) -> None:
        """Add or update a connection configuration."""
        config.validate()
        self.connections[config.id] = config
    
    def remove_connection(self, connection_id: str) -> bool:
        """Remove a connection configuration."""
        if connection_id in self.connections:
            del self.connections[connection_id]
            return True
        return False
    
    @classmethod
    def ensure_global_config_dir(cls) -> None:
        """Ensure the global config directory exists."""
        cls.GLOBAL_CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    
    @classmethod
    def save_global_config(cls, configs: List[ConnectionConfig]) -> None:
        """Save configurations to global config file."""
        cls.ensure_global_config_dir()
        
        data = {
            "connections": [config.to_dict() for config in configs]
        }
        
        with open(cls.GLOBAL_CONFIG_FILE, 'w') as f:
            json.dump(data, f, indent=2)


"""Tests for configuration loader."""

import pytest
import json
import tempfile
from pathlib import Path
from remoteshell_mcp.config_loader import ConfigLoader, ConnectionConfig


def test_connection_config_from_dict():
    """Test creating ConnectionConfig from dictionary."""
    data = {
        "id": "test",
        "host": "localhost",
        "user": "testuser",
        "port": 22,
        "auth_type": "password",
        "password": "testpass"
    }
    config = ConnectionConfig.from_dict(data)
    
    assert config.id == "test"
    assert config.host == "localhost"
    assert config.user == "testuser"
    assert config.port == 22
    assert config.auth_type == "password"
    assert config.password == "testpass"


def test_connection_config_validation():
    """Test connection config validation."""
    # Valid password auth
    config = ConnectionConfig(
        id="test",
        host="localhost",
        user="user",
        auth_type="password",
        password="pass"
    )
    config.validate()  # Should not raise
    
    # Valid key auth
    config = ConnectionConfig(
        id="test",
        host="localhost",
        user="user",
        auth_type="key",
        key_path="~/.ssh/id_rsa"
    )
    config.validate()  # Should not raise
    
    # Invalid: no password for password auth
    with pytest.raises(ValueError):
        config = ConnectionConfig(
            id="test",
            host="localhost",
            user="user",
            auth_type="password"
        )
        config.validate()
    
    # Invalid: no key for key auth
    with pytest.raises(ValueError):
        config = ConnectionConfig(
            id="test",
            host="localhost",
            user="user",
            auth_type="key"
        )
        config.validate()


def test_config_loader_with_server_args():
    """Test loading connections from server args."""
    server_args = {
        "connections": [
            {
                "id": "test1",
                "host": "host1",
                "user": "user1",
                "auth_type": "password",
                "password": "pass1"
            },
            {
                "id": "test2",
                "host": "host2",
                "user": "user2",
                "auth_type": "key",
                "key_path": "/path/to/key"
            }
        ]
    }
    
    loader = ConfigLoader(server_args=server_args)
    
    assert len(loader.list_connections()) == 2
    assert loader.get_connection("test1") is not None
    assert loader.get_connection("test2") is not None
    
    config1 = loader.get_connection("test1")
    assert config1.host == "host1"
    assert config1.user == "user1"


def test_config_loader_add_remove():
    """Test adding and removing connections."""
    loader = ConfigLoader()
    
    config = ConnectionConfig(
        id="new",
        host="newhost",
        user="newuser",
        auth_type="password",
        password="newpass"
    )
    
    loader.add_connection(config)
    assert loader.get_connection("new") is not None
    
    success = loader.remove_connection("new")
    assert success is True
    assert loader.get_connection("new") is None
    
    success = loader.remove_connection("nonexistent")
    assert success is False


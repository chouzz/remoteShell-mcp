"""SSH client wrapper using Paramiko."""

import os
import stat
import io
from pathlib import Path
from typing import Dict, Any, Optional, Tuple
import paramiko
from paramiko import SSHClient, AutoAddPolicy, RSAKey, Ed25519Key, ECDSAKey
from paramiko.ssh_exception import SSHException, AuthenticationException


class SSHConnectionError(Exception):
    """SSH connection error."""
    pass


class SSHCommandError(Exception):
    """SSH command execution error."""
    pass


class SSHFileTransferError(Exception):
    """SSH file transfer error."""
    pass


class RemoteSSHClient:
    """Wrapper around Paramiko SSHClient for simplified SSH operations."""
    
    def __init__(
        self,
        host: str,
        user: str,
        port: int = 22,
        password: Optional[str] = None,
        private_key: Optional[str] = None,
        timeout: int = 30
    ):
        """
        Initialize SSH client.
        
        Args:
            host: Remote host address
            user: Username for authentication
            port: SSH port (default: 22)
            password: Password for authentication (optional)
            key_path: Path to SSH private key file (optional)
            timeout: Connection timeout in seconds
        """
        self.host = host
        self.user = user
        self.port = port
        self.password = password
        self.private_key = private_key
        self.timeout = timeout
        
        self._client: Optional[SSHClient] = None
        self._sftp: Optional[paramiko.SFTPClient] = None

    def _load_private_key(self, value: str):
        """Load a Paramiko PKey either from a file path or from PEM text."""
        expanded = os.path.expanduser(value)
        key_classes = [RSAKey, Ed25519Key, ECDSAKey]

        # Prefer treating it as a path if it exists.
        if os.path.exists(expanded):
            key_error: Optional[Exception] = None
            for key_class in key_classes:
                try:
                    return key_class.from_private_key_file(expanded)
                except Exception as e:
                    key_error = e
            raise SSHConnectionError(f"Failed to load SSH private key from file: {key_error}")

        # Otherwise treat it as key text.
        key_error = None
        for key_class in key_classes:
            try:
                return key_class.from_private_key(io.StringIO(value))
            except Exception as e:
                key_error = e
        raise SSHConnectionError(f"Failed to load SSH private key from text: {key_error}")
    
    def connect(self) -> None:
        """Establish SSH connection."""
        if self._client is not None:
            # Already connected
            return
        
        try:
            self._client = SSHClient()
            self._client.set_missing_host_key_policy(AutoAddPolicy())
            
            # Prepare connection parameters
            connect_kwargs = {
                "hostname": self.host,
                "port": self.port,
                "username": self.user,
                "timeout": self.timeout,
                "allow_agent": False,
                "look_for_keys": False,
            }
            
            # Add authentication method
            if self.private_key:
                connect_kwargs["pkey"] = self._load_private_key(self.private_key)
            
            elif self.password:
                # Use password authentication
                connect_kwargs["password"] = self.password
            
            else:
                raise SSHConnectionError("Either password or private_key must be provided")
            
            # Connect
            self._client.connect(**connect_kwargs)
            
        except AuthenticationException as e:
            raise SSHConnectionError(f"Authentication failed: {e}")
        except SSHException as e:
            raise SSHConnectionError(f"SSH connection failed: {e}")
        except Exception as e:
            raise SSHConnectionError(f"Connection error: {e}")
    
    def disconnect(self) -> None:
        """Close SSH connection."""
        if self._sftp:
            try:
                self._sftp.close()
            except:
                pass
            self._sftp = None
        
        if self._client:
            try:
                self._client.close()
            except:
                pass
            self._client = None
    
    def is_connected(self) -> bool:
        """Check if SSH connection is active."""
        if self._client is None:
            return False
        
        try:
            transport = self._client.get_transport()
            return transport is not None and transport.is_active()
        except:
            return False
    
    def ensure_connected(self) -> None:
        """Ensure the connection is active, reconnect if necessary."""
        if not self.is_connected():
            self.disconnect()
            self.connect()
    
    def execute_command(
        self,
        command: str,
        timeout: Optional[int] = None,
        working_dir: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Execute a command on the remote host.
        
        Args:
            command: Command to execute
            timeout: Command timeout in seconds
            working_dir: Working directory for command execution
        
        Returns:
            Dictionary with stdout, stderr, and exit_code
        """
        self.ensure_connected()
        
        try:
            # Add working directory change if specified
            if working_dir:
                command = f"cd {working_dir} && {command}"
            
            # Execute command
            stdin, stdout, stderr = self._client.exec_command(
                command,
                timeout=timeout or self.timeout
            )
            
            # Read output
            stdout_data = stdout.read().decode('utf-8', errors='replace')
            stderr_data = stderr.read().decode('utf-8', errors='replace')
            exit_code = stdout.channel.recv_exit_status()
            
            return {
                "stdout": stdout_data,
                "stderr": stderr_data,
                "exit_code": exit_code,
                "success": exit_code == 0
            }
        
        except Exception as e:
            raise SSHCommandError(f"Command execution failed: {e}")
    
    def _get_sftp(self) -> paramiko.SFTPClient:
        """Get or create SFTP client."""
        self.ensure_connected()
        
        if self._sftp is None:
            try:
                self._sftp = self._client.open_sftp()
            except Exception as e:
                raise SSHFileTransferError(f"Failed to open SFTP session: {e}")
        
        return self._sftp
    
    def upload_file(
        self,
        local_path: str,
        remote_path: str
    ) -> Dict[str, Any]:
        """
        Upload a file to the remote host.
        
        Args:
            local_path: Local file path
            remote_path: Remote file path
        
        Returns:
            Dictionary with success status and file info
        """
        local_path = os.path.expanduser(local_path)
        
        if not os.path.exists(local_path):
            raise SSHFileTransferError(f"Local file not found: {local_path}")
        
        if not os.path.isfile(local_path):
            raise SSHFileTransferError(f"Path is not a file: {local_path}")
        
        try:
            sftp = self._get_sftp()

            # If remote_path is a directory path, keep the local filename.
            if remote_path.endswith("/"):
                remote_path = remote_path + os.path.basename(local_path)
            else:
                try:
                    st = sftp.stat(remote_path)
                    if stat.S_ISDIR(st.st_mode):
                        remote_path = remote_path.rstrip("/") + "/" + os.path.basename(local_path)
                except FileNotFoundError:
                    # Treat as file path that may not exist yet.
                    pass
            
            # Upload file
            sftp.put(local_path, remote_path)
            
            # Get file info
            local_size = os.path.getsize(local_path)
            remote_stat = sftp.stat(remote_path)
            
            return {
                "success": True,
                "local_path": local_path,
                "remote_path": remote_path,
                "size": local_size,
                "uploaded": remote_stat.st_size == local_size
            }
        
        except Exception as e:
            raise SSHFileTransferError(f"File upload failed: {e}")
    
    def download_file(
        self,
        remote_path: str,
        local_path: str
    ) -> Dict[str, Any]:
        """
        Download a file from the remote host.
        
        Args:
            remote_path: Remote file path
            local_path: Local file path
        
        Returns:
            Dictionary with success status and file info
        """
        local_path = os.path.expanduser(local_path)
        if os.path.isdir(local_path) or local_path.endswith(os.sep):
            local_path = os.path.join(local_path, os.path.basename(remote_path))
        
        # Create local directory if it doesn't exist
        local_dir = os.path.dirname(local_path)
        if local_dir:
            os.makedirs(local_dir, exist_ok=True)
        
        try:
            sftp = self._get_sftp()
            
            # Check if remote file exists
            try:
                remote_stat = sftp.stat(remote_path)
            except FileNotFoundError:
                raise SSHFileTransferError(f"Remote file not found: {remote_path}")
            
            # Download file
            sftp.get(remote_path, local_path)
            
            # Get file info
            local_size = os.path.getsize(local_path)
            
            return {
                "success": True,
                "remote_path": remote_path,
                "local_path": local_path,
                "size": local_size,
                "downloaded": local_size == remote_stat.st_size
            }
        
        except SSHFileTransferError:
            raise
        except Exception as e:
            raise SSHFileTransferError(f"File download failed: {e}")
    
    def __enter__(self):
        """Context manager entry."""
        self.connect()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.disconnect()
    
    def __del__(self):
        """Cleanup on deletion."""
        self.disconnect()


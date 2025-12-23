"""Test command validator integration with server tools."""

import pytest
import os
from unittest.mock import patch, MagicMock

from remoteshell_mcp.command_validator import CommandValidator, DangerousCommandError


class TestCommandValidatorIntegration:
    """Test that CommandValidator is properly integrated into server tools."""

    def test_command_validator_blocks_dangerous_commands(self):
        """Test that CommandValidator blocks dangerous commands."""
        # Dangerous commands that should be blocked
        dangerous_commands = [
            "rm -rf /",
            "rm -rf /*",
            "rm -rf /root",
            "dd if=/dev/zero of=/dev/sda",
            "mkfs.ext4 /dev/sda",
            "halt",
            "shutdown -h now",
            ":(){ :|:& };:",
        ]

        for command in dangerous_commands:
            with pytest.raises(DangerousCommandError):
                CommandValidator.validate(command)

    def test_command_validator_allows_safe_commands(self):
        """Test that CommandValidator allows safe commands."""
        # Safe commands that should be allowed
        safe_commands = [
            "ls -la",
            "df -h",
            "ps aux",
            "cat /etc/hostname",
            "echo hello world",
            "mkdir test_dir",
            "cp file1 file2",
            "grep pattern file.txt",
        ]

        for command in safe_commands:
            # Should not raise any exception
            CommandValidator.validate(command)

    def test_command_validator_can_be_bypassed_via_env_var(self, monkeypatch):
        """Test that validation can be bypassed via environment variable."""
        # Set environment variable to disable validation
        monkeypatch.setenv('REMOTESHELL_DISABLE_VALIDATION', '1')

        # Even dangerous commands should not raise exception when validation is disabled
        dangerous_command = "rm -rf /"
        CommandValidator.validate(dangerous_command)  # Should not raise

        # Clean up
        monkeypatch.delenv('REMOTESHELL_DISABLE_VALIDATION', raising=False)

    def test_server_integration_imports_validator(self):
        """Test that server.py properly imports CommandValidator."""
        try:
            from remoteshell_mcp.server import CommandValidator as ServerCommandValidator
            from remoteshell_mcp.server import DangerousCommandError as ServerDangerousCommandError
            # Import successful
            assert ServerCommandValidator is not None
            assert ServerDangerousCommandError is not None
        except ImportError:
            pytest.fail("CommandValidator or DangerousCommandError not properly imported in server.py")

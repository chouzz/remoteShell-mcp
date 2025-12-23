"""Command validator to prevent execution of dangerous commands."""

import os
import re
from typing import List, Tuple


class DangerousCommandError(Exception):
    """Raised when a dangerous command is detected."""
    pass


class CommandValidator:
    """Validates commands to prevent execution of dangerous operations."""
    
    # List of dangerous command patterns: each tuple contains (pattern, description)
    DANGEROUS_PATTERNS: List[Tuple[str, str]] = [
        # Remove root directory (exact match)
        (r'\brm\s+.*-.*rf\s+/\s*$', 'Remove root directory'),
        (r'\brm\s+.*-.*rf\s+/\s+', 'Remove root directory'),
        (r'\brm\s+.*-.*rf\s+/\*', 'Remove all files under root directory'),
        (r'\brm\s+.*-.*rf\s+/\s*\*', 'Remove all files under root directory'),
        
        # Remove critical system directories (exact match, only matches directory itself, not files under it)
        (r'\brm\s+.*-.*rf\s+/root(?:\s|$)', 'Remove /root directory'),
        (r'\brm\s+.*-.*rf\s+/etc(?:\s|$)', 'Remove /etc directory'),
        (r'\brm\s+.*-.*rf\s+/usr(?:\s|$)', 'Remove /usr directory'),
        (r'\brm\s+.*-.*rf\s+/bin(?:\s|$)', 'Remove /bin directory'),
        (r'\brm\s+.*-.*rf\s+/sbin(?:\s|$)', 'Remove /sbin directory'),
        (r'\brm\s+.*-.*rf\s+/lib(?:\s|$)', 'Remove /lib directory'),
        (r'\brm\s+.*-.*rf\s+/var(?:\s|$)', 'Remove /var directory'),
        (r'\brm\s+.*-.*rf\s+/sys(?:\s|$)', 'Remove /sys directory'),
        (r'\brm\s+.*-.*rf\s+/proc(?:\s|$)', 'Remove /proc directory'),
        (r'\brm\s+.*-.*rf\s+/dev(?:\s|$)', 'Remove /dev directory'),
        (r'\brm\s+.*-.*rf\s+/boot(?:\s|$)', 'Remove /boot directory'),
        
        # Format commands
        (r'\bmkfs\b', 'Format filesystem'),
        (r'\bfdisk\b', 'Disk partitioning operation'),
        (r'\bparted\b', 'Disk partitioning operation'),
        
        # Destructive dd commands
        (r'\bdd\s+.*if=.*of=/dev/', 'Destructive dd command'),
        (r'\bdd\s+.*if=/dev/zero', 'dd command using /dev/zero'),
        (r'\bdd\s+.*if=/dev/urandom', 'dd command using /dev/urandom'),
        
        # Critical system operations
        (r'\bchmod\s+.*777\s+.*/', 'Modify root directory permissions'),
        (r'\bchown\s+.*root\s+.*/', 'Modify root directory ownership'),
        
        # Other dangerous operations
        (r'>\s*/dev/', 'Redirect to device file'),
        (r':\(\)\s*\{\s*:\s*\|\s*:\s*&\s*\}\s*;', 'Fork bomb'),
        (r'\bhalt\b', 'System halt'),
        (r'\bpoweroff\b', 'System poweroff'),
        (r'\breboot\b', 'System reboot'),
        (r'\bshutdown\b', 'System shutdown'),
        
        # Patterns for removing all files (but allow relative paths like ./test)
        (r'\brm\s+.*-.*rf\s+\*', 'Remove all files in current directory'),
        (r'\brm\s+.*-.*rf\s+\.\.(?:\s|$|/)', 'Remove parent directory'),
    ]
    
    @classmethod
    def validate(cls, command: str) -> None:
        """
        Validate if a command is safe to execute.
        
        Args:
            command: Command string to execute
            
        Raises:
            DangerousCommandError: If a dangerous command is detected
            
        Note:
            Validation can be bypassed by setting the REMOTESHELL_DISABLE_VALIDATION
            environment variable to any non-empty value.
        """
        if not command or not command.strip():
            return
        
        # Skip validation if REMOTESHELL_DISABLE_VALIDATION environment variable is set
        if os.environ.get('REMOTESHELL_DISABLE_VALIDATION'):
            return
        
        # Normalize command: remove extra spaces, convert to lowercase for matching
        normalized_command = ' '.join(command.split())
        command_lower = normalized_command.lower()
        
        # Check if matches dangerous patterns
        for pattern, description in cls.DANGEROUS_PATTERNS:
            if re.search(pattern, command_lower, re.IGNORECASE):
                raise DangerousCommandError(
                    f"Dangerous command detected: {description}\n"
                    f"Command: {command}\n"
                    f"Pattern: {pattern}"
                )
        
        # Additional check: prevent bypassing through variables or quotes
        # Check if command contains obvious dangerous operations (use word boundaries for exact matching)
        dangerous_keywords_patterns = [
            (r'\brm\s+-rf\s+/\s*$', 'rm -rf /'),
            (r'\brm\s+-rf\s+/\s+', 'rm -rf /'),
            (r'\brm\s+-rf\s+/\*', 'rm -rf /*'),
            (r'\brm\s+-rf\s+/root\b', 'rm -rf /root'),
            (r'\bdd\s+.*if=/dev/zero\b', 'dd if=/dev/zero'),
        ]
        
        for pattern, keyword_desc in dangerous_keywords_patterns:
            if re.search(pattern, command_lower, re.IGNORECASE):
                raise DangerousCommandError(
                    f"Dangerous command keyword detected: {keyword_desc}\n"
                    f"Command: {command}"
                )

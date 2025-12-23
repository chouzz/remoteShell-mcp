"""Command validator to prevent execution of dangerous commands."""

import re
from typing import List, Tuple


class DangerousCommandError(Exception):
    """Raised when a dangerous command is detected."""
    pass


class CommandValidator:
    """Validates commands to prevent execution of dangerous operations."""
    
    # 危险命令模式列表：每个元组包含 (模式, 描述)
    DANGEROUS_PATTERNS: List[Tuple[str, str]] = [
        # 删除根目录（精确匹配）
        (r'\brm\s+.*-.*rf\s+/\s*$', '删除根目录'),
        (r'\brm\s+.*-.*rf\s+/\s+', '删除根目录'),
        (r'\brm\s+.*-.*rf\s+/\*', '删除根目录下所有文件'),
        (r'\brm\s+.*-.*rf\s+/\s*\*', '删除根目录下所有文件'),
        
        # 删除系统关键目录（精确匹配，只匹配目录本身，不匹配目录下的文件）
        (r'\brm\s+.*-.*rf\s+/root(?:\s|$)', '删除/root目录'),
        (r'\brm\s+.*-.*rf\s+/etc(?:\s|$)', '删除/etc目录'),
        (r'\brm\s+.*-.*rf\s+/usr(?:\s|$)', '删除/usr目录'),
        (r'\brm\s+.*-.*rf\s+/bin(?:\s|$)', '删除/bin目录'),
        (r'\brm\s+.*-.*rf\s+/sbin(?:\s|$)', '删除/sbin目录'),
        (r'\brm\s+.*-.*rf\s+/lib(?:\s|$)', '删除/lib目录'),
        (r'\brm\s+.*-.*rf\s+/var(?:\s|$)', '删除/var目录'),
        (r'\brm\s+.*-.*rf\s+/sys(?:\s|$)', '删除/sys目录'),
        (r'\brm\s+.*-.*rf\s+/proc(?:\s|$)', '删除/proc目录'),
        (r'\brm\s+.*-.*rf\s+/dev(?:\s|$)', '删除/dev目录'),
        (r'\brm\s+.*-.*rf\s+/boot(?:\s|$)', '删除/boot目录'),
        
        # 格式化命令
        (r'\bmkfs\b', '格式化文件系统'),
        (r'\bfdisk\b', '磁盘分区操作'),
        (r'\bparted\b', '磁盘分区操作'),
        
        # 破坏性dd命令
        (r'\bdd\s+.*if=.*of=/dev/', '破坏性dd命令'),
        (r'\bdd\s+.*if=/dev/zero', '使用/dev/zero的dd命令'),
        (r'\bdd\s+.*if=/dev/urandom', '使用/dev/urandom的dd命令'),
        
        # 系统关键操作
        (r'\bchmod\s+.*777\s+.*/', '修改根目录权限'),
        (r'\bchown\s+.*root\s+.*/', '修改根目录所有者'),
        
        # 其他危险操作
        (r'>\s*/dev/', '重定向到设备文件'),
        (r':\(\)\s*\{\s*:\s*\|\s*:\s*&\s*\}\s*;', 'Fork炸弹'),
        (r'\bhalt\b', '系统关机'),
        (r'\bpoweroff\b', '系统关机'),
        (r'\breboot\b', '系统重启'),
        (r'\bshutdown\b', '系统关机'),
        
        # 删除所有文件的模式（但允许相对路径如 ./test）
        (r'\brm\s+.*-.*rf\s+\*', '删除当前目录所有文件'),
        (r'\brm\s+.*-.*rf\s+\.\.(?:\s|$|/)', '删除上级目录'),
    ]
    
    # 允许的危险命令白名单（如果需要的话，可以在这里添加例外情况）
    ALLOWED_PATTERNS: List[str] = [
        # 可以在这里添加允许的模式
    ]
    
    @classmethod
    def validate(cls, command: str) -> None:
        """
        验证命令是否安全。
        
        Args:
            command: 要执行的命令字符串
            
        Raises:
            DangerousCommandError: 如果检测到危险命令
        """
        if not command or not command.strip():
            return
        
        # 标准化命令：去除多余空格，转换为小写进行匹配
        normalized_command = ' '.join(command.split())
        command_lower = normalized_command.lower()
        
        # 检查是否匹配白名单
        for allowed_pattern in cls.ALLOWED_PATTERNS:
            if re.search(allowed_pattern, command_lower, re.IGNORECASE):
                return
        
        # 检查是否匹配危险模式
        for pattern, description in cls.DANGEROUS_PATTERNS:
            if re.search(pattern, command_lower, re.IGNORECASE):
                raise DangerousCommandError(
                    f"检测到危险命令: {description}\n"
                    f"命令: {command}\n"
                    f"模式: {pattern}"
                )
        
        # 额外检查：防止通过变量或引号绕过检查
        # 检查命令中是否包含明显的危险操作（使用单词边界确保精确匹配）
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
                    f"检测到危险命令关键词: {keyword_desc}\n"
                    f"命令: {command}"
                )

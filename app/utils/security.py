import re
from pathlib import Path


def sanitize_file_path(file_path: str) -> bool:
    if not file_path:
        return False
    
    if ".." in file_path:
        return False
    
    if Path(file_path).is_absolute():
        return False
    
    dangerous_patterns = [r"^/", r"^\\", r"^[A-Za-z]:", r"\x00"]
    for pattern in dangerous_patterns:
        if re.search(pattern, file_path):
            return False
    
    return True


def sanitize_command(command: str) -> bool:
    if not command:
        return False
    
    dangerous_chars = [";", "|", "&", "$", "`", "()", "&&", "||"]
    for char in dangerous_chars:
        if char in command:
            return False
    
    dangerous_patterns = [r"\$\(", r"`"]
    for pattern in dangerous_patterns:
        if re.search(pattern, command):
            return False
    
    return True


import os
from pathlib import Path
from typing import Set

def find_python_files(root_dir: str, exclude_patterns: Set[str] = None) -> Set[Path]:
    """Find all Python files in directory, excluding test files and examples"""
    if exclude_patterns is None:
        exclude_patterns = {'test', 'example', 'sample'}
        
    python_files = set()
    
    for root, _, files in os.walk(root_dir):
        if any(x in root.lower() for x in exclude_patterns):
            continue
            
        for file in files:
            if file.endswith('.py') and not any(x in file.lower() for x in exclude_patterns):
                python_files.add(Path(root) / file)
                
    return python_files 
import os
from typing import List, Dict
from prefect import task

def get_directory_tree(start_path: str) -> List[str]:
    """Get a list of all files in the directory tree."""
    files = []
    for root, _, filenames in os.walk(start_path):
        for filename in filenames:
            # Get relative path from start_path
            full_path = os.path.join(root, filename)
            rel_path = os.path.relpath(full_path, start_path)
            files.append(rel_path)
    return files

def detect_languages(files: List[str]) -> Dict[str, int]:
    """Detect programming languages based on file extensions."""
    extensions = {}
    for file in files:
        ext = os.path.splitext(file)[1].lower()
        if ext:  # Skip files without extensions
            extensions[ext] = extensions.get(ext, 0) + 1
    return extensions

def find_package_files(local_path: str) -> Dict[str, str]:
    """Find and read package manager files."""
    package_files = {
        'npm': 'package.json',
        'python': 'requirements.txt',
        'ruby': 'Gemfile',
        'php': 'composer.json',
        'rust': 'Cargo.toml',
    }
    
    found_files = {}
    for pkg_type, filename in package_files.items():
        file_path = os.path.join(local_path, filename)
        if os.path.exists(file_path):
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    found_files[pkg_type] = f.read()
            except Exception as e:
                print(f"Error reading {filename}: {e}")
    return found_files

def read_readme(local_path: str) -> str:
    """Find and read README file."""
    readme_variants = ['README.md', 'README.MD', 'Readme.md', 'readme.md']
    for readme in readme_variants:
        readme_path = os.path.join(local_path, readme)
        if os.path.exists(readme_path):
            try:
                with open(readme_path, 'r', encoding='utf-8') as f:
                    return f.read()
            except Exception as e:
                print(f"Error reading README: {e}")
    return ""

@task
def discover_project(local_path: str) -> dict:
    """
    Analyze a local repository to discover project information.
    
    Args:
        local_path (str): Path to the local repository
        
    Returns:
        dict: Dictionary containing discovered project information
    """
    print(f"Starting project discovery for path: {local_path}")
    
    # Get file tree
    files = get_directory_tree(local_path)
    
    project_info = {
        "path": local_path,
        "base_directory": os.path.basename(local_path),
        "file_tree": files,
        "languages": detect_languages(files),
        "package_files": find_package_files(local_path),
        "readme": read_readme(local_path),
        "file_count": len(files)
    }
    
    print(f"Discovery complete. Found project info: {project_info}")
    return project_info

# TODO
# - identify frameworks ie spring-boot, hibernate
# - treesitter parser
# - more sophisticated data flow tracking with train tracking, inter-procedure analysis, etc
# - additional entrypoint types - database, message queue, RPC, etc
# - enhanved trust boundaries - network etc
# - visualization graphs and diagrams
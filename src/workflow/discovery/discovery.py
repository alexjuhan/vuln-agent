import os
from typing import List, Dict, Optional
from prefect import task
from .ast_analysis.analyzers.base import BaseAnalyzer
from .ast_analysis.analyzers.flask_analyzer import FlaskAnalyzer

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

def detect_frameworks(files: List[str], package_files: Dict[str, str]) -> List[str]:
    """Detect frameworks used in the project based on files and dependencies."""
    frameworks = set()  # Use a set to avoid duplicates
    
    # Check package files for framework dependencies
    if 'python' in package_files:
        reqs = package_files['python'].lower()
        if 'flask' in reqs and not any(f.endswith('flask.py') for f in files):
            frameworks.add('flask')
        if 'django' in reqs and any(f in files for f in ['manage.py', 'wsgi.py']):
            frameworks.add('django')
        if 'fastapi' in reqs:
            frameworks.add('fastapi')
    
    # For Flask specifically, look for app patterns but exclude test files
    flask_patterns = [
        f for f in files 
        if f.endswith('.py') 
        and not f.startswith('test') 
        and not '/tests/' in f
        and any(pattern in f.lower() for pattern in ['app.py', 'application.py', 'wsgi.py'])
    ]
    
    if flask_patterns:
        frameworks.add('flask')
    
    return list(frameworks)

def get_analyzer_for_framework(framework: str) -> Optional[BaseAnalyzer]:
    """Get the appropriate analyzer for a given framework."""
    analyzer_map = {
        'flask': FlaskAnalyzer,
        # Comment out unimplemented analyzers for now
        # 'django': DjangoAnalyzer,
        # 'fastapi': FastAPIAnalyzer,
    }
    
    analyzer_class = analyzer_map.get(framework)
    return analyzer_class() if analyzer_class else None

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
    package_files = find_package_files(local_path)
    
    # Detect frameworks
    frameworks = detect_frameworks(files, package_files)
    
    # Run framework-specific analysis
    framework_analysis = {}
    for framework in frameworks:
        analyzer = get_analyzer_for_framework(framework)
        if analyzer:
            print(f"Running analysis for framework: {framework}")
            try:
                # Filter relevant Python files
                relevant_files = [
                    f for f in files 
                    if f.endswith('.py') 
                    and not f.startswith('test')
                    and not '/tests/' in f
                    and not '/examples/' in f
                ]
                
                # Analyze Python files
                for file in relevant_files:
                    file_path = os.path.join(local_path, file)
                    print(f"Analyzing file: {file_path}")
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            content = f.read()
                            analyzer.analyze(content, file_path)
                    except Exception as e:
                        print(f"Error analyzing file {file_path}: {str(e)}")
                        import traceback
                        traceback.print_exc()
                
                # Only add analysis results if we found something
                if analyzer.entry_points or analyzer.data_flows:
                    framework_analysis[framework] = {
                        'entry_points': list(analyzer.entry_points),
                        'data_flows': [flow.to_dict() for flow in analyzer.data_flows],
                        'variables': list(analyzer.scope_variables)
                    }
                    print(f"Found analysis results for {framework}:")
                    print(f"Entry points: {analyzer.entry_points}")
                    print(f"Data flows: {analyzer.data_flows}")
                else:
                    print(f"No analysis results found for {framework}")
                    
            except Exception as e:
                print(f"Error analyzing {framework} framework: {str(e)}")
                import traceback
                traceback.print_exc()
    
    project_info = {
        "path": local_path,
        "base_directory": os.path.basename(local_path),
        "file_tree": files,
        "languages": detect_languages(files),
        "package_files": package_files,
        "readme": read_readme(local_path),
        "file_count": len(files),
        "frameworks": frameworks,
        "framework_analysis": framework_analysis
    }
    
    # Write project info to JSON file in scanner root directory
    scanner_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
    output_path = os.path.join(scanner_root, 'project_discovery.json')
    try:
        import json
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(project_info, f, indent=2, sort_keys=True)
        print(f"Project info written to: {output_path}")
    except Exception as e:
        print(f"Error writing project info to file: {str(e)}")
    
    print(f"Discovery complete. Found project info: {project_info}")
    return project_info

# TODO
# - identify frameworks ie spring-boot, hibernate
# - treesitter parser
# - more sophisticated data flow tracking with train tracking, inter-procedure analysis, etc
# - additional entrypoint types - database, message queue, RPC, etc
# - enhanved trust boundaries - network etc
# - visualization graphs and diagrams
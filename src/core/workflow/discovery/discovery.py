import os
from typing import List, Dict, Optional
from prefect import task
from .ast_analysis.analyzers.base import BaseAnalyzer
from .ast_analysis.analyzers.flask_analyzer import FlaskAnalyzer
from .ast_analysis.analyzers.express_analyzer import ExpressAnalyzer

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
        'python': ['requirements.txt', 'pyproject.toml'],
        'ruby': 'Gemfile',
        'php': 'composer.json',
        'rust': 'Cargo.toml',
    }
    
    found_files = {}
    for pkg_type, filenames in package_files.items():
        # Convert single filename to list for consistent handling
        if isinstance(filenames, str):
            filenames = [filenames]
            
        for filename in filenames:
            file_path = os.path.join(local_path, filename)
            if os.path.exists(file_path):
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        # Store with filename as key to distinguish between multiple files
                        found_files[f"{pkg_type}:{filename}"] = f.read()
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
    print("\n=== Starting Framework Detection ===")
    frameworks = set()
    
    # Check Python package files for framework dependencies
    python_files = [f for f in package_files.keys() if f.startswith('python:')]
    print(f"Found Python package files: {python_files}")
    
    for python_file in python_files:
        reqs = package_files[python_file].lower()
        print(f"Analyzing requirements in {python_file}")
        
        if 'flask' in reqs:
            print("Found Flask in requirements")
            if not any(f.endswith('flask.py') for f in files):
                frameworks.add('flask')
                print("Added Flask framework")
        
        if 'django' in reqs:
            print("Found Django in requirements")
            if any(f in files for f in ['manage.py', 'wsgi.py']):
                frameworks.add('django')
                print("Added Django framework")
                
        if 'fastapi' in reqs:
            frameworks.add('fastapi')
            print("Added FastAPI framework")

    # Check package.json files
    npm_files = [f for f in package_files.keys() if f.endswith('package.json')]
    print(f"\nFound NPM package files: {npm_files}")
    
    for npm_file in npm_files:
        try:
            import json
            package_json = json.loads(package_files[npm_file])
            dependencies = {
                **package_json.get('dependencies', {}),
                **package_json.get('devDependencies', {})
            }
            scripts = package_json.get('scripts', {})
            
            # Check for common Node.js frameworks
            if 'next' in dependencies:
                frameworks.add('nextjs')
            if 'express' in dependencies:
                frameworks.add('express')
            if 'react' in dependencies or 'react-dom' in dependencies:
                frameworks.add('react')
            if 'vue' in dependencies:
                frameworks.add('vue')
            if '@nestjs/core' in dependencies:
                frameworks.add('nestjs')
            if 'gatsby' in dependencies:
                frameworks.add('gatsby')
            if 'nuxt' in dependencies:
                frameworks.add('nuxt')
            
            # Enhanced Angular detection
            if '@angular/core' in dependencies:
                frameworks.add('angular')
            elif any('ng ' in cmd for cmd in scripts.values()):  # Look for Angular CLI commands
                frameworks.add('angular')
            
        except json.JSONDecodeError:
            print(f"Error parsing {npm_file}")
    
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
    
    # Look for framework-specific files and patterns
    for file in files:
        file_lower = file.lower()
        # Next.js patterns
        if any(pattern in file_lower for pattern in ['next.config.js', 'pages/_app.js', 'pages/_app.tsx']):
            frameworks.add('nextjs')
        # Express.js patterns
        if file_lower.endswith(('app.js', 'server.js', 'index.js')):
            file_content = package_files.get(file, '')
            if 'express' in file_content.lower():
                frameworks.add('express')
        # Angular patterns
        if any(pattern in file_lower for pattern in ['angular.json', '.angular-cli.json', 'ng-module.ts']):
            frameworks.add('angular')
    
    return list(frameworks)

def get_analyzer_for_framework(framework: str) -> Optional[BaseAnalyzer]:
    """Get the appropriate analyzer for a given framework."""
    analyzer_map = {
        'flask': FlaskAnalyzer,
        'express': ExpressAnalyzer,
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
    print("\n=== Starting Project Discovery ===")
    print(f"Analyzing path: {local_path}")
    
    print("\nGathering file tree...")
    files = get_directory_tree(local_path)
    print(f"Found {len(files)} files")
    
    print("\nReading package files...")
    package_files = find_package_files(local_path)
    print(f"Found package files: {list(package_files.keys())}")
    
    print("\nDetecting frameworks...")
    frameworks = detect_frameworks(files, package_files)
    print(f"Detected frameworks: {frameworks}")
    
    print("\nStarting framework-specific analysis...")
    framework_analysis = {}
    for framework in frameworks:
        analyzer = get_analyzer_for_framework(framework)
        if analyzer:
            print(f"\nAnalyzing {framework} framework...")
            try:
                # Filter relevant files based on framework
                if framework == 'express':
                    relevant_files = [
                        f for f in files 
                        if f.endswith(('.js', '.ts')) 
                        and not f.startswith('test')
                        and not '/tests/' in f
                        and not '/frontend/' in f
                        and not 'spec.' in f
                        and ('/routes/' in f  # Focus on routes directory
                             or 'app.ts' in f  # Main application file
                             or 'server.ts' in f)  # Server setup file
                    ]
                    print(f"Found {len(relevant_files)} relevant Express files")
                else:
                    relevant_files = []
                
                # Analyze files
                for file in relevant_files:
                    file_path = os.path.join(local_path, file)
                    print(f"\nAnalyzing file: {file}")
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            content = f.read()
                            analyzer.analyze(content, file_path)
                    except Exception as e:
                        print(f"Error analyzing file {file}: {str(e)}")
                
                # Store analysis results
                if analyzer.entry_points or analyzer.data_flows:
                    framework_analysis[framework] = {
                        'entry_points': list(analyzer.entry_points),
                        'data_flows': [flow.to_dict() for flow in analyzer.data_flows],
                        'variables': list(analyzer.scope_variables)
                    }
                    print(f"\nAnalysis results for {framework}:")
                    print(f"Entry points: {len(analyzer.entry_points)}")
                    print(f"Data flows: {len(analyzer.data_flows)}")
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
#        "readme": read_readme(local_path),
        "file_count": len(files),
        "frameworks": frameworks,
        "framework_analysis": framework_analysis
    }
    
    # Write project info to JSON file in scanner root directory
    scanner_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
    output_path = os.path.join(scanner_root, 'project_context.json')
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
# - more sophisticated data flow tracking with train tracking, inter-procedure analysis, etc
# - additional entrypoint types - database, message queue, RPC, etc
# - enhanced trust boundaries - network etc
# - treesitter parser
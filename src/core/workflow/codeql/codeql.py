import os
import subprocess
from typing import Dict, Optional
from prefect import task

def determine_main_language(languages: Dict[str, int]) -> Optional[str]:
    """
    Determine the main programming language based on file extensions.
    
    Args:
        languages (Dict[str, int]): Dictionary of language extensions and their counts
        
    Returns:
        Optional[str]: The main language for CodeQL analysis, or None if not supported
    """
    # Map of file extensions to CodeQL language identifiers
    extension_to_language = {
        '.py': 'python',
        '.js': 'javascript',
        '.ts': 'javascript',
        '.jsx': 'javascript',
        '.tsx': 'javascript',
        '.java': 'java',
        '.cpp': 'cpp',
        '.cc': 'cpp',
        '.cxx': 'cpp',
        '.c': 'cpp',
        '.hpp': 'cpp',
        '.h': 'cpp',
        '.cs': 'csharp',
        '.go': 'go',
        '.rb': 'ruby'
    }
    
    # Count occurrences by CodeQL language
    language_counts = {}
    for ext, count in languages.items():
        if ext in extension_to_language:
            ql_lang = extension_to_language[ext]
            language_counts[ql_lang] = language_counts.get(ql_lang, 0) + count
    
    # Find the language with the most files
    if not language_counts:
        return None
        
    return max(language_counts.items(), key=lambda x: x[1])[0]

@task
def build_codeql_database(project_path: str, languages: Dict[str, int]) -> Optional[str]:
    """
    Build a CodeQL database for the main programming language in the project.
    
    Args:
        project_path (str): Path to the project root
        languages (Dict[str, int]): Dictionary of language extensions and their counts
        
    Returns:
        Optional[str]: Path to the created database, or None if failed
    """
    print("\n=== Starting CodeQL Database Creation ===")
    
    # Determine the main language
    main_language = determine_main_language(languages)
    if not main_language:
        print("No supported language found for CodeQL analysis")
        return None
    
    print(f"Main language detected: {main_language}")
    
    # Create database name from project directory name
    db_name = f"{os.path.basename(project_path)}_db"
    
    # Construct the database path in the project directory
    db_path = os.path.join(project_path, db_name)
    
    # Build the CodeQL database creation command
    cmd = [
        "./codeql",  # CodeQL binary at root directory
        "database",
        "create",
        "--language=" + main_language,
        "--source-root=" + project_path,
        db_path
    ]
    
    print(f"Running CodeQL command: {' '.join(cmd)}")
    
    try:
        # Run the CodeQL database creation command
        result = subprocess.run(
            cmd,
            check=True,
            capture_output=True,
            text=True
        )
        print("Database creation output:", result.stdout)
        
        if os.path.exists(db_path):
            print(f"Successfully created CodeQL database at: {db_path}")
            return db_path
        else:
            print("Database creation failed: database directory not found")
            return None
            
    except subprocess.CalledProcessError as e:
        print(f"Error creating CodeQL database: {str(e)}")
        print("Error output:", e.stderr)
        return None
    except Exception as e:
        print(f"Unexpected error creating CodeQL database: {str(e)}")
        return None

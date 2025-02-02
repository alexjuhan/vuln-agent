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
        "codeql",  # CodeQL binary at root directory
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

@task
def run_codeql_analysis(database_path: str, main_language: str) -> Optional[str]:
    """
    Run CodeQL analysis on the created database and generate SARIF output.
    
    Args:
        database_path (str): Path to the CodeQL database
        main_language (str): The main programming language of the project
        
    Returns:
        Optional[str]: Path to the SARIF output file, or None if analysis failed
    """
    print("\n=== Starting CodeQL Analysis ===")
    
    # Generate output file path
    project_dir = os.path.dirname(database_path)
    project_name = os.path.basename(os.path.dirname(database_path))
    sarif_path = os.path.join(project_dir, f"{project_name}-analysis.sarif")
    
    # Build the CodeQL analysis command
    cmd = [
        "codeql",
        "database",
        "analyze",
        "--format=sarif-latest",
        f"--output={sarif_path}",
        "--",
        database_path,
        f"codeql/{main_language}-queries"
    ]
    
    print(f"Running CodeQL analysis command: {' '.join(cmd)}")
    
    try:
        # Run the CodeQL analysis command
        result = subprocess.run(
            cmd,
            check=True,
            capture_output=True,
            text=True
        )
        print("Analysis output:", result.stdout)
        
        if os.path.exists(sarif_path):
            print(f"Successfully created SARIF output at: {sarif_path}")
            return sarif_path
        else:
            print("Analysis failed: SARIF output file not found")
            return None
            
    except subprocess.CalledProcessError as e:
        print(f"Error running CodeQL analysis: {str(e)}")
        print("Error output:", e.stderr)
        return None
    except Exception as e:
        print(f"Unexpected error during CodeQL analysis: {str(e)}")
        return None

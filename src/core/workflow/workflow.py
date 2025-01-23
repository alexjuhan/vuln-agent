from prefect import flow, task
import git
from core.workflow.discovery.discovery import discover_project
from core.workflow.codeql.codeql import build_codeql_database

@task
def clone_repo(repo_url: str, local_path: str):
    """Clone a GitHub repository to the specified local path."""
    print(f"Starting to clone repository from {repo_url} to {local_path}")
    try:
        git.Repo.clone_from(repo_url, local_path)
        print("Repository cloned successfully")
        return True
    except Exception as e:
        print(f"Error cloning repository: {e}")
        return False

@flow
def security_scan_workflow(repo_url: str, local_path: str):
    """Main workflow that starts with cloning the repository and runs discovery."""
    print(f"Starting security scan workflow for repository: {repo_url}")
    
    # First step: Clone the repository
    print("Step 1: Cloning repository...")
    clone_success = clone_repo(repo_url, local_path)
    
    if not clone_success:
        print("Repository cloning failed, stopping workflow")
        raise Exception("Failed to clone repository")
    
    # Second step: Run discovery on the cloned repository
    print("Step 2: Running project discovery...")
    project_info = discover_project(local_path)
    print(f"Project discovery completed. Found info: {project_info}")
    
    # Third step: Build CodeQL database
    print("Step 3: Building CodeQL database...")
    database_path = build_codeql_database(local_path, project_info["languages"])
    if not database_path:
        print("CodeQL database creation failed")
        raise Exception("Failed to create CodeQL database")
    
    # Add database path to project info
    project_info["codeql_database"] = database_path
    
    return project_info

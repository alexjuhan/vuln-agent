from prefect import flow, task
import git
from workflow.discovery.discovery import discover_project

@task
def clone_repo(repo_url: str, local_path: str):
    """Clone a GitHub repository to the specified local path."""
    try:
        git.Repo.clone_from(repo_url, local_path)
        return True
    except Exception as e:
        print(f"Error cloning repository: {e}")
        return False

@flow
def security_scan_workflow(repo_url: str, local_path: str):
    """Main workflow that starts with cloning the repository and runs discovery."""
    # First step: Clone the repository
    clone_success = clone_repo(repo_url, local_path)
    
    if not clone_success:
        raise Exception("Failed to clone repository")
    
    # Second step: Run discovery on the cloned repository
    project_info = discover_project(local_path)
    
    return project_info

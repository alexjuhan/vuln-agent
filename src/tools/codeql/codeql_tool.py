from src.tools.base.base_tool import SecurityAnalysisTool
import asyncio
import docker
from pathlib import Path

class CodeQLTool(SecurityAnalysisTool):
    def __init__(self):
        super().__init__()
        self.name = "codeql"
        self.description = "CodeQL static analysis tool"
        self.parameters = {
            "repo_path": "Path to the repository to analyze",
            "query_suite": "Name of the query suite to run"
        }
        self.client = docker.from_client()
        
    async def execute(self, repo_path: str, query_suite: str = "security-extended") -> dict:
        """Execute CodeQL analysis using Docker container"""
        try:
            container = await self._run_container(repo_path, query_suite)
            results = await self._parse_results(container)
            return {
                "tool": self.name,
                "findings": results,
                "status": "success"
            }
        except Exception as e:
            return {
                "tool": self.name,
                "error": str(e),
                "status": "failed"
            }
            
    async def _run_container(self, repo_path: str, query_suite: str):
        repo_abs_path = str(Path(repo_path).resolve())
        return self.client.containers.run(
            "ghcr.io/microsoft/cstsectools-codeql-container:latest",
            command=f"codeql database create db --language=python \
                     && codeql database analyze db {query_suite} --format=sarif-latest",
            volumes={
                repo_abs_path: {'bind': '/src', 'mode': 'ro'}
            },
            remove=True
        ) 
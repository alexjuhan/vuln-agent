from typing import List, Dict
from ..base_tool import BaseTool
import docker
import tempfile
import os

class SemgrepTool(BaseTool):
    name = "semgrep"
    description = "Semgrep security analyzer"
    
    def __init__(self):
        self.client = docker.from_env()
        self.container_name = "security_agent_semgrep"
        
    async def execute(self, source_path: str) -> Dict:
        with tempfile.TemporaryDirectory() as temp_dir:
            # Mount paths for Docker
            volumes = {
                source_path: {'bind': '/src', 'mode': 'ro'},
                temp_dir: {'bind': '/output', 'mode': 'rw'},
                f"{os.path.dirname(__file__)}/rules": {'bind': '/rules', 'mode': 'ro'}
            }
            
            try:
                container = self.client.containers.run(
                    image="returntocorp/semgrep",
                    command=f"--config=/rules/security --json --output=/output/results.json /src",
                    volumes=volumes,
                    remove=True,
                    detach=True
                )
                
                # Wait for completion and get results
                container.wait()
                with open(f"{temp_dir}/results.json", 'r') as f:
                    results = json.load(f)
                
                return self._process_results(results)
                
            except docker.errors.ContainerError as e:
                raise ToolExecutionError(f"Semgrep analysis failed: {str(e)}") 
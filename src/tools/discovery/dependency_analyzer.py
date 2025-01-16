from ..base.discovery_tool import DiscoveryTool
from typing import Dict, Any
import subprocess
import json

class DependencyAnalyzerTool(DiscoveryTool):
    """Analyzes project dependencies and their versions"""
    
    async def analyze(self, path: str) -> Dict[str, Any]:
        findings = {
            "direct_dependencies": {},
            "transitive_dependencies": {},
            "vulnerable_dependencies": []
        }
        
        # Check for package managers
        if await self._has_file(path, "requirements.txt"):
            findings.update(await self._analyze_python_deps(path))
        if await self._has_file(path, "package.json"):
            findings.update(await self._analyze_node_deps(path))
            
        return findings
    
    async def _analyze_python_deps(self, path: str) -> Dict[str, Any]:
        try:
            result = subprocess.run(
                ["pip", "list", "--format=json"],
                capture_output=True,
                text=True
            )
            return {"python_dependencies": json.loads(result.stdout)}
        except:
            return {"python_dependencies": {}} 
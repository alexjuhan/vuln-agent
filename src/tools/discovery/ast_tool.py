from smolagents import Tool
from typing import Dict, Any
from pathlib import Path
import ast

class CodeAnalyzerTool(Tool):
    name = "code_analyzer"
    description = "Analyzes project structure, entry points, and data flows"
    """Analyzes project structure, entry points, and data flows"""
    
    async def analyze(self, path: str) -> Dict[str, Any]:
        findings = {
            "entry_points": [],
            "data_flows": [],
            "tech_stack": {
                "languages": set(),
                "frameworks": set()
            }
        }
        
        # Recursively analyze project files
        for file_path in Path(path).rglob("*"):
            if file_path.is_file():
                await self._analyze_file(file_path, findings)
                
        # Convert sets to lists for JSON serialization
        findings["tech_stack"]["languages"] = list(findings["tech_stack"]["languages"])
        findings["tech_stack"]["frameworks"] = list(findings["tech_stack"]["frameworks"])
        
        return findings
        
    async def _analyze_file(self, file_path: Path, findings: Dict[str, Any]):
        # Detect language and frameworks
        if file_path.suffix == ".py":
            findings["tech_stack"]["languages"].add("Python")
            await self._analyze_python_file(file_path, findings)
        elif file_path.suffix == ".js":
            findings["tech_stack"]["languages"].add("JavaScript")
            await self._analyze_js_file(file_path, findings) 
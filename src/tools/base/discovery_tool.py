from .base_tool import SecurityAnalysisTool
from typing import Dict, Any

class DiscoveryTool(SecurityAnalysisTool):
    """Base class for project discovery tools"""
    
    async def analyze(self, path: str) -> Dict[str, Any]:
        """Analyze specific aspect of the project"""
        raise NotImplementedError
        
    async def validate_findings(self, findings: Dict[str, Any]) -> Dict[str, Any]:
        """Validate and clean up discovery findings"""
        return findings 
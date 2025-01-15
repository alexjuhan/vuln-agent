from ..base.discovery_tool import DiscoveryTool
from typing import Dict, Any
import yaml
import json
from pathlib import Path

class ConfigAnalyzerTool(DiscoveryTool):
    """Analyzes project configuration files for security settings"""
    
    async def analyze(self, path: str) -> Dict[str, Any]:
        findings = {
            "security_config": {},
            "environment_vars": [],
            "secrets_management": {},
            "compliance_settings": {}
        }
        
        # Look for common config files
        config_files = [
            ".env",
            "config.yaml",
            "config.json",
            "docker-compose.yml",
            ".gitlab-ci.yml",
            ".github/workflows"
        ]
        
        for config in config_files:
            config_path = Path(path) / config
            if config_path.exists():
                findings["security_config"][config] = await self._analyze_config(config_path)
                
        return findings 
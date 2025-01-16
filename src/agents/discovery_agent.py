from dataclasses import dataclass
from typing import Dict, List, Any
from pathlib import Path
from .base_agent import BaseSecurityAgent
from src.tools.base.base_tool import BaseTool
from src.tools.discovery.dependency_analyzer import DependencyAnalyzerTool
from src.tools.discovery.code_analyzer import CodeAnalyzerTool
from src.tools.discovery.config_analyzer import ConfigAnalyzerTool
from .prompts.system_prompt import DISCOVERY_AGENT_PROMPT

@dataclass
class ProjectContext:
    tech_stack: Dict[str, Any]         # Technologies, frameworks, languages
    project_type: str                  # Web app, API, CLI tool, etc.
    entry_points: List[Dict[str, Any]] # API endpoints, CLI commands, UI entry points
    data_flows: List[Dict[str, Any]]   # Data flow paths through the application
    dependencies: Dict[str, str]       # Direct and transitive dependencies
    security_requirements: List[str]   # Security requirements or compliance needs
    threat_model: Dict[str, Any]       # Basic threat model based on context
    test_coverage: Dict[str, float]    # Existing test coverage metrics

class DiscoveryAgent(BaseSecurityAgent):
    @classmethod
    async def create(cls, llm_config: dict, tools: List[BaseTool]) -> 'DiscoveryAgent':
        discovery_tools = [
            DependencyAnalyzerTool(),
            CodeAnalyzerTool(),
            ConfigAnalyzerTool()
        ]
        llm_config["prompt"] = DISCOVERY_AGENT_PROMPT
        return await super().create(llm_config, discovery_tools + tools)

    async def analyze_project(self, repo_path: str) -> ProjectContext:
        """Perform comprehensive project discovery"""
        # Gather raw data using the specialized analyzer tools
        tech_data = await self._analyze_tech_stack(repo_path)
        deps_data = await self._analyze_dependencies(repo_path)
        structure_data = await self._analyze_project_structure(repo_path)
        
        # Enhance context prompt with detailed tool findings
        context_prompt = await self._generate_context_prompt(
            tech_data, deps_data, structure_data
        )
        
        analysis = await self.agent_executor.run(context_prompt)
        
        # Generate threat model based on comprehensive analysis
        threat_model = await self._generate_threat_model(analysis)
        
        # Generate testing strategy with coverage targets
        test_coverage = await self._generate_test_plan(analysis, threat_model)
        
        return ProjectContext(
            tech_stack=tech_data["tech_stack"],  # Now using direct tool output
            project_type=analysis["project_type"],
            entry_points=tech_data["entry_points"],  # Direct from CodeAnalyzerTool
            data_flows=tech_data["data_flows"],     # Direct from CodeAnalyzerTool
            dependencies=deps_data["direct_dependencies"],  # Direct from DependencyAnalyzerTool
            security_requirements=analysis["security_requirements"],
            threat_model=threat_model,
            test_coverage=test_coverage
        )

    async def _generate_test_plan(self, analysis: Dict[str, Any], threat_model: Dict[str, Any]) -> Dict[str, float]:
        """Generate a security testing strategy based on project context and threat model"""
        test_plan_prompt = f"""
        Based on the detailed project analysis and threat model:
        - Tech stack: {analysis['tech_stack']}
        - Project type: {analysis['project_type']}
        - Entry points: {analysis['entry_points']}
        - Data flows: {analysis['data_flows']}
        - Critical threats: {threat_model['critical_threats']}
        - Trust boundaries: {threat_model['trust_boundaries']}
        
        Create a comprehensive security testing strategy that:
        1. Prioritizes critical components and data flows identified in the threat model
        2. Selects appropriate security testing tools for each component
        3. Defines custom CodeQL queries needed for unique patterns
        4. Identifies areas requiring manual security review
        5. Specifies required testing coverage percentages by component
        """
        
        return await self.agent_executor.run(test_plan_prompt)

    async def _analyze_tech_stack(self, repo_path: str) -> Dict[str, Any]:
        """Analyze the project's technology stack using CodeAnalyzerTool"""
        code_analyzer = next(t for t in self.tools if isinstance(t, CodeAnalyzerTool))
        return await code_analyzer.analyze(repo_path)

    async def _analyze_dependencies(self, repo_path: str) -> Dict[str, Any]:
        """Analyze project dependencies using DependencyAnalyzerTool"""
        dep_analyzer = next(t for t in self.tools if isinstance(t, DependencyAnalyzerTool))
        return await dep_analyzer.analyze(repo_path)

    async def _analyze_project_structure(self, repo_path: str) -> Dict[str, Any]:
        """Analyze project configuration and structure"""
        config_analyzer = next(t for t in self.tools if isinstance(t, ConfigAnalyzerTool))
        config_data = await config_analyzer.analyze(repo_path)
        
        return {
            "config": config_data,
            "security_settings": config_data.get("security_config", {}),
            "environment": config_data.get("environment_vars", []),
            "ci_cd": any(key in config_data.get("security_config", {}) 
                        for key in [".gitlab-ci.yml", ".github/workflows"])
        }

    async def _generate_context_prompt(self, tech_data: Dict[str, Any], 
                                     deps_data: Dict[str, Any], 
                                     structure_data: Dict[str, Any]) -> str:
        """Generate a detailed prompt incorporating all analyzer findings"""
        return f"""
        Analyze this project's security context based on comprehensive tool findings:

        Technical Stack Analysis:
        - Languages: {tech_data['tech_stack']['languages']}
        - Frameworks: {tech_data['tech_stack']['frameworks']}
        - Entry Points: {tech_data['entry_points']}
        - Data Flows: {tech_data['data_flows']}

        Dependency Analysis:
        - Direct Dependencies: {deps_data['direct_dependencies']}
        - Transitive Dependencies: {deps_data['transitive_dependencies']}
        - Vulnerable Dependencies: {deps_data['vulnerable_dependencies']}

        Configuration Analysis:
        - Security Settings: {structure_data['security_config']}
        - Environment Variables: {structure_data['environment_vars']}
        - Secrets Management: {structure_data['secrets_management']}
        - Compliance Settings: {structure_data['compliance_settings']}
        - CI/CD Present: {structure_data.get('ci_cd', False)}

        Please analyze and provide:
        1. Project type classification
        2. Security requirements based on context
        3. Key entry points and data flows
        4. Initial threat model considerations
        """ 
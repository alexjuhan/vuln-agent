from dataclasses import dataclass
from typing import Dict, List, Any
from pathlib import Path
from .base_agent import BaseSecurityAgent

@dataclass
class ProjectContext:
    tech_stack: Dict[str, Any]        # Technologies, frameworks, languages
    project_type: str                 # Web app, API, CLI tool, etc.
    entry_points: List[Dict[str, Any]] # API endpoints, CLI commands, UI entry points
    data_flows: List[Dict[str, Any]]   # Data flow paths through the application
    dependencies: Dict[str, str]       # Direct and transitive dependencies
    security_requirements: List[str]    # Security requirements or compliance needs
    threat_model: Dict[str, Any]       # Basic threat model based on context
    test_coverage: Dict[str, float]    # Existing test coverage metrics

class DiscoveryAgent(BaseSecurityAgent):
    def __init__(self, llm_config: dict, tools: List[BaseTool]):
        discovery_tools = [
            DependencyAnalyzerTool(),
            CodeAnalyzerTool(),
            ConfigAnalyzerTool(),
            TestCoverageAnalyzerTool()
        ]
        super().__init__(llm_config, discovery_tools)

    async def analyze_project(self, repo_path: str) -> ProjectContext:
        """Perform comprehensive project discovery"""
        # Gather raw data
        tech_data = await self._analyze_tech_stack(repo_path)
        deps_data = await self._analyze_dependencies(repo_path)
        structure_data = await self._analyze_project_structure(repo_path)
        
        # Use LLM to synthesize findings into context
        context_prompt = self._generate_context_prompt(
            tech_data, deps_data, structure_data
        )
        
        analysis = await self.agent_executor.run(context_prompt)
        
        # Generate testing strategy
        test_plan = await self._generate_test_plan(analysis)
        
        return ProjectContext(
            tech_stack=analysis["tech_stack"],
            project_type=analysis["project_type"],
            entry_points=analysis["entry_points"],
            data_flows=analysis["data_flows"],
            dependencies=deps_data,
            security_requirements=analysis["security_requirements"],
            threat_model=await self._generate_threat_model(analysis),
            test_coverage=test_plan
        )

    async def _generate_test_plan(self, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Generate a security testing strategy based on project context"""
        test_plan_prompt = f"""
        Based on the project analysis:
        - Tech stack: {analysis['tech_stack']}
        - Project type: {analysis['project_type']}
        - Entry points: {analysis['entry_points']}
        - Data flows: {analysis['data_flows']}
        
        Create a security testing strategy that:
        1. Prioritizes critical components and data flows
        2. Selects appropriate security testing tools
        3. Defines custom CodeQL queries needed
        4. Identifies areas needing manual review
        5. Estimates required testing coverage
        """
        
        return await self.agent_executor.run(test_plan_prompt) 
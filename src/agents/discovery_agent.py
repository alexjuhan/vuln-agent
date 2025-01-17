from dataclasses import dataclass
from typing import Dict, List, Any
from smolagents import CodeAgent, HfApiAgent
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

discoveryAgent = CodeAgent(
    tools=[],
    model=HfApiAgent("meta-llama/Meta-Llama-3.1-8B-Instruct"),
    additional_authorized_imports=['ast', 'pipdeptree', ],
)
 
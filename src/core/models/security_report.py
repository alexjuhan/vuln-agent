from dataclasses import dataclass
from typing import List, Dict, Optional
from enum import Enum

class Severity(Enum):
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"

@dataclass
class Finding:
    vulnerability_type: str
    severity: Severity
    affected_package: Optional[str]
    code_snippet: Optional[str]
    file_path: Optional[str]
    line_number: Optional[int]
    description: str
    
    @classmethod
    def from_tool_results(cls, tool_name: str, results: Dict) -> List['Finding']:
        """Convert tool-specific results into Finding objects"""
        findings = []
        for result in results:
            findings.append(cls(
                vulnerability_type=result.get('type'),
                severity=Severity(result.get('severity', 'MEDIUM').upper()),
                affected_package=result.get('package'),
                code_snippet=result.get('code'),
                file_path=result.get('file'),
                line_number=result.get('line'),
                description=result.get('description')
            ))
        return findings
    
    def to_prompt_format(self) -> str:
        """Format finding for LLM prompt"""
        return f"""Type: {self.vulnerability_type}
Severity: {self.severity.value}
Package: {self.affected_package or 'N/A'}
Location: {self.file_path}:{self.line_number if self.line_number else 'N/A'}
Description: {self.description}
Code: {self.code_snippet or 'N/A'}
"""

@dataclass
class Context:
    _contexts: Dict[Finding, Dict] = None
    
    def __init__(self):
        self._contexts = {}
    
    def add_finding_context(self, finding: Finding, similar_code: List[str], cve_info: Dict):
        """Add context for a specific finding"""
        self._contexts[finding] = {
            'similar_code': similar_code,
            'cve_info': cve_info
        }
    
    def to_string(self) -> str:
        """Convert context to string format for LLM prompt"""
        context_strings = []
        for finding, context in self._contexts.items():
            context_strings.append(f"""
Finding: {finding.vulnerability_type}
Similar Code Patterns:
{chr(10).join(context['similar_code'])}
CVE Information:
{context['cve_info']}
""")
        return "\n".join(context_strings)

@dataclass
class SecurityReport:
    critical_findings: List[Finding]
    high_priority_findings: List[Finding]
    medium_priority_findings: List[Finding]
    low_priority_findings: List[Finding]
    analysis_summary: str
    
    @classmethod
    def from_analysis(cls, analysis: Dict) -> 'SecurityReport':
        """Create report from LLM analysis output"""
        return cls(
            critical_findings=[Finding(**f) for f in analysis.get('critical', [])],
            high_priority_findings=[Finding(**f) for f in analysis.get('high', [])],
            medium_priority_findings=[Finding(**f) for f in analysis.get('medium', [])],
            low_priority_findings=[Finding(**f) for f in analysis.get('low', [])],
            analysis_summary=analysis.get('summary', '')
        ) 
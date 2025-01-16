from typing import Dict, List, Any
from ...agents.vulnerability_agent import VulnerabilityAnalysisAgent
from ...agents.triage_agent import TriageAgent
from ...core.models.security_report import SecurityReport, Finding, Context
from ..models.database import Finding, SecurityReport

class SecurityAnalysisWorkflow:
    def __init__(self, llm_config: Dict):
        self.llm_config = llm_config
        
    async def execute_analysis(self, repo_path: str) -> SecurityReport:
        """Execute the full security analysis workflow"""
        try:
            # 1. Initialize Agents
            vuln_agent = VulnerabilityAnalysisAgent()
            triage_agent = TriageAgent(self.llm_config, [])
            
            # 2. Run Vulnerability Analysis
            security_report = await vuln_agent.analyze_codebase(repo_path)
            
            # 3. Triage and Score Findings
            scored_findings = await triage_agent.analyze_findings(
                security_report.findings
            )
            
            # 4. Update report with scored findings
            return await self._generate_final_report(
                security_report,
                scored_findings
            )
            
        except Exception as e:
            # Log error and cleanup
            raise RuntimeError(f"Analysis failed: {str(e)}")
    
    async def _generate_final_report(
        self,
        initial_report: SecurityReport,
        scored_findings: Dict[str, float]
    ) -> SecurityReport:
        """Generate final report with prioritized findings"""
        
        # Update findings with confidence scores
        for finding in initial_report.findings:
            finding_id = finding.get("id") or finding.get("ruleId")
            finding.confidence_score = scored_findings.get(finding_id, 0.0)
        
        # Sort findings by confidence score
        initial_report.findings.sort(
            key=lambda x: x.confidence_score,
            reverse=True
        )
        
        # Group findings by severity
        findings_by_severity = self._group_findings_by_severity(
            initial_report.findings
        )
        
        return SecurityReport(
            findings=findings_by_severity,
            context=initial_report.context,
            metadata={
                **initial_report.metadata,
                "analysis_summary": self._generate_summary(findings_by_severity)
            }
        )
    
    def _group_findings_by_severity(
        self,
        findings: List[Finding]
    ) -> Dict[str, List[Finding]]:
        """Group findings by severity considering confidence scores"""
        severity_groups = {
            "critical": [],
            "high": [],
            "medium": [],
            "low": []
        }
        
        for finding in findings:
            # Adjust severity based on confidence score
            adjusted_severity = self._adjust_severity(
                finding.severity,
                finding.confidence_score
            )
            severity_groups[adjusted_severity].append(finding)
            
        return severity_groups
    
    def _adjust_severity(self, base_severity: str, confidence: float) -> str:
        """Adjust finding severity based on confidence score"""
        severity_levels = ["low", "medium", "high", "critical"]
        base_index = severity_levels.index(base_severity.lower())
        
        # Potentially adjust severity down if confidence is low
        if confidence < 0.3 and base_index > 0:
            return severity_levels[base_index - 1]
        # Potentially adjust severity up if confidence is very high
        elif confidence > 0.8 and base_index < len(severity_levels) - 1:
            return severity_levels[base_index + 1]
            
        return base_severity
    
    def _generate_summary(
        self,
        findings_by_severity: Dict[str, List[Finding]]
    ) -> Dict[str, Any]:
        """Generate analysis summary statistics"""
        return {
            "total_findings": sum(
                len(findings) for findings in findings_by_severity.values()
            ),
            "findings_by_severity": {
                severity: len(findings)
                for severity, findings in findings_by_severity.items()
            },
            "average_confidence": self._calculate_average_confidence(
                [f for findings in findings_by_severity.values() 
                 for f in findings]
            )
        } 
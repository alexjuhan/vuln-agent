from typing import Dict, List
from ...analyzers.manager import AnalyzerManager
from ...agents.vulnerability_agent import VulnerabilityAnalysisAgent
from ...core.models.security_report import SecurityReport, Finding, Context
from ..models.database import Finding, SecurityReport, create_finding_from_tool_result

class VulnerabilityAnalysisWorkflow:
    def __init__(self, agent: VulnerabilityAnalysisAgent):
        self.agent = agent
        self.analyzer_manager = AnalyzerManager()
        
    async def execute_analysis(self, repo_path: str) -> SecurityReport:
        try:
            # Initialize analyzers
            await self.analyzer_manager.initialize_analyzers()
            
            # 1. Initial SAST Scan
            sast_results = await self._run_sast_analysis(repo_path)
            
            # 2. Dependency Analysis
            deps_results = await self._run_dependency_analysis(repo_path)
            
            # 3. Context Analysis
            context = await self._analyze_context(repo_path, sast_results)
            
            # 4. LLM Analysis and Prioritization
            return await self._generate_prioritized_report(
                sast_results, 
                deps_results, 
                context
            )
        finally:
            # Ensure cleanup happens even if analysis fails
            await self.analyzer_manager.cleanup()
    
    async def _run_sast_analysis(self, repo_path: str) -> List[Finding]:
        """Run all SAST analyzers through the manager"""
        raw_results = await self.analyzer_manager.run_analysis(repo_path)
        
        # Convert raw results to Finding objects
        findings = []
        for tool_name, tool_results in raw_results.items():
            for result in tool_results:
                finding = create_finding_from_tool_result(tool_name, result)
                findings.append(finding)
        
        return findings
    
    async def _run_dependency_analysis(self, repo_path: str) -> Dict:
        """Run dependency analysis tools"""
        return await self.analyzer_manager.run_dependency_analysis(repo_path)
    
    async def _analyze_context(self, repo_path: str, findings: List[Finding]) -> Context:
        """Analyze the context of findings using vector DB and code analysis"""
        context = Context()
        
        for finding in findings:
            # Get code context from vector DB
            similar_code = await self.agent.tools.vector_db.query_similar_code(
                finding.code_snippet
            )
            
            # Get CVE information
            cve_info = await self.agent.tools.cve_lookup.search(
                finding.vulnerability_type,
                finding.affected_package
            )
            
            context.add_finding_context(finding, similar_code, cve_info)
            
        return context
    
    async def _generate_prioritized_report(
        self,
        sast_results: List[Finding],
        deps_results: Dict,
        context: Context
    ) -> SecurityReport:
        """Use the LLM agent to analyze and prioritize findings"""
        
        # Generate analysis prompt with all context
        analysis_prompt = f"""
        Analyze these security findings:
        
        SAST Findings:
        {self._format_findings(sast_results)}
        
        Dependency Analysis:
        {deps_results}
        
        Context Analysis:
        {context.to_string()}
        
        Generate a prioritized security report with:
        1. Critical vulnerabilities requiring immediate attention
        2. High priority issues
        3. Medium priority concerns
        4. Low priority findings
        
        For each finding, provide:
        - Detailed impact analysis
        - Exploitability assessment
        - Specific remediation steps
        - Links to relevant CVEs and OWASP guidelines
        """
        
        # Get LLM analysis
        analysis = await self.agent.analyze(analysis_prompt)
        
        # Convert to structured report
        return SecurityReport.from_analysis(analysis)
    
    def _format_findings(self, findings: List[Finding]) -> str:
        """Format findings for LLM prompt"""
        return "\n".join(
            f"Finding {i+1}:\n{finding.to_prompt_format()}"
            for i, finding in enumerate(findings)
        ) 
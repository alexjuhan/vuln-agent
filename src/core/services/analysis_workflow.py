class VulnerabilityAnalysisWorkflow:
    def __init__(self, agent: VulnerabilityAnalysisAgent):
        self.agent = agent
        
    async def execute_analysis(self, repo_path: str) -> SecurityReport:
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
from dataclasses import dataclass
from typing import Dict, List
from pathlib import Path
from .base_agent import BaseSecurityAgent
from src.tools.base_tool import BaseTool

@dataclass
class FindingContext:
    source_file: str
    source_lines: List[str]
    ast_context: dict
    similar_patterns: List[dict]
    sanitizer_analysis: dict

class TriageAgent(BaseSecurityAgent):
    def __init__(self, llm_config: dict, tools: List[BaseTool]):
        super().__init__(llm_config, tools)
        self.analysis_cache = {}
        
    async def analyze_findings(self, findings: List[dict]) -> Dict[str, float]:
        """Analyze and score security findings"""
        scored_findings = {}
        
        for finding in findings:
            analysis = await self._analyze_finding(finding)
            confidence_score = self._calculate_confidence_score(analysis)
            finding_id = finding.get("id") or finding.get("ruleId")
            scored_findings[finding_id] = confidence_score
            
        return scored_findings
    
    async def _analyze_finding(self, finding: dict) -> dict:
        """Analyze a single finding with enhanced context"""
        context = await self._get_finding_context(finding)
        
        # Enhanced pattern analysis
        ast_patterns = await self._analyze_patterns(context)
        similar_patterns = await self.vector_db.query_similar_code(
            context.source_lines,
            pattern_type=finding.get("category")
        )
        
        # Add data flow analysis
        data_flow = await self._analyze_data_flow(context)
        sanitizer_analysis = await self._analyze_sanitizers(context)
        
        return {
            "finding": finding,
            "context": context,
            "ast_patterns": ast_patterns,
            "similar_patterns": similar_patterns,
            "data_flow": data_flow,
            "sanitizer_analysis": sanitizer_analysis
        }

    def _calculate_confidence_score(self, analysis: dict) -> float:
        """Enhanced confidence scoring with data flow consideration"""
        score = 0.0
        
        # Data flow analysis weight
        if analysis["data_flow"].get("reaches_sink", False):
            score += 0.4
        if analysis["data_flow"].get("has_sanitization", False):
            score -= 0.3
            
        # Existing pattern weights
        if analysis["ast_patterns"].get("has_validation", False):
            score += 0.2
        if analysis["sanitizer_analysis"].get("effectiveness", 0) > 0.7:
            score -= 0.2
            
        # Similar pattern analysis
        safe_patterns = sum(1 for p in analysis["similar_patterns"] 
                          if p.get("is_safe", False))
        if analysis["similar_patterns"]:
            pattern_score = (safe_patterns / len(analysis["similar_patterns"])) * 0.2
            score += pattern_score
            
        return max(0.0, min(1.0, score))

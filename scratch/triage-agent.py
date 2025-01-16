import json
from dataclasses import dataclass
from typing import List, Dict, Optional
import numpy as np
from pathlib import Path

@dataclass
class FindingContext:
    source_file: str
    source_lines: List[str]
    ast_context: dict
    similar_patterns: List[dict]
    sanitizer_analysis: dict

class CodeQLTriageAgent:
    def __init__(self, vector_db, codeql_db):
        self.vector_db = vector_db
        self.codeql_db = codeql_db
        self.analysis_cache = {}
        
    async def analyze_sarif(self, sarif_path: Path) -> Dict[str, float]:
        """Analyze SARIF output and return confidence scores for each finding"""
        with open(sarif_path) as f:
            sarif_data = json.load(f)
            
        findings = []
        for run in sarif_data["runs"]:
            for result in run["results"]:
                finding = await self._analyze_finding(result)
                findings.append(finding)
                
        return self._score_findings(findings)
    
    async def _analyze_finding(self, result: dict) -> dict:
        """Analyze a single SARIF finding"""
        # Get source context
        location = result["locations"][0]["physicalLocation"]
        source_file = location["artifactLocation"]["uri"]
        source_region = location["region"]
        
        # Get relevant source code
        context = await self._get_context(source_file, source_region)
        
        # Analyze AST patterns
        ast_patterns = await self._analyze_ast_patterns(context)
        
        # Find similar code patterns
        similar = await self._find_similar_patterns(context)
        
        # Analyze sanitization
        sanitizers = await self._analyze_sanitizers(context)
        
        return {
            "result": result,
            "context": context,
            "ast_patterns": ast_patterns,
            "similar_patterns": similar,
            "sanitizer_analysis": sanitizers
        }
    
    async def _get_context(self, file: str, region: dict) -> FindingContext:
        """Get source code context around finding"""
        source_lines = self.vector_db.get_file_lines(file)
        start_line = max(0, region["startLine"] - 5)
        end_line = min(len(source_lines), region["endLine"] + 5)
        
        context_lines = source_lines[start_line:end_line]
        
        ast_context = self.codeql_db.get_ast_node(file, region["startLine"])
        
        return FindingContext(
            source_file=file,
            source_lines=context_lines,
            ast_context=ast_context,
            similar_patterns=[],
            sanitizer_analysis={}
        )
    
    async def _analyze_ast_patterns(self, context: FindingContext) -> dict:
        """Analyze AST patterns to identify common safe/unsafe patterns"""
        ast_node = context.ast_context
        
        # Look for validation patterns
        validation_patterns = {
            "input_validation": self._check_input_validation(ast_node),
            "sanitizer_calls": self._check_sanitizer_calls(ast_node),
            "framework_protection": self._check_framework_protection(ast_node)
        }
        
        # Look for unsafe patterns
        unsafe_patterns = {
            "direct_use": self._check_direct_use(ast_node),
            "missing_validation": self._check_missing_validation(ast_node),
            "weak_sanitization": self._check_weak_sanitization(ast_node)
        }
        
        return {
            "validation_patterns": validation_patterns,
            "unsafe_patterns": unsafe_patterns
        }
    
    async def _find_similar_patterns(self, context: FindingContext) -> List[dict]:
        """Find similar code patterns in the codebase"""
        # Get vector embedding of context
        context_embedding = self.vector_db.embed_code("\n".join(context.source_lines))
        
        # Find similar code
        similar = self.vector_db.find_similar(context_embedding, limit=5)
        
        # Analyze similar patterns
        patterns = []
        for code in similar:
            pattern = {
                "code": code,
                "safety_analysis": self._analyze_pattern_safety(code)
            }
            patterns.append(pattern)
            
        return patterns
    
    async def _analyze_sanitizers(self, context: FindingContext) -> dict:
        """Analyze sanitization patterns"""
        sanitizers = {
            "framework_sanitizers": self._find_framework_sanitizers(context),
            "custom_sanitizers": self._find_custom_sanitizers(context),
            "sanitizer_effectiveness": self._analyze_sanitizer_effectiveness(context)
        }
        return sanitizers
    
    def _score_findings(self, findings: List[dict]) -> Dict[str, float]:
        """Score likelihood of false positives"""
        scores = {}
        for finding in findings:
            score = self._calculate_confidence_score(finding)
            finding_id = finding["result"]["ruleId"]
            scores[finding_id] = score
        return scores
    
    def _calculate_confidence_score(self, finding: dict) -> float:
        """Calculate confidence score for a finding"""
        score = 0.0
        
        # Check for strong validation patterns
        if finding["ast_patterns"]["validation_patterns"]["input_validation"]:
            score += 0.3
            
        if finding["ast_patterns"]["validation_patterns"]["sanitizer_calls"]:
            score += 0.2
            
        if finding["ast_patterns"]["validation_patterns"]["framework_protection"]:
            score += 0.2
            
        # Check for unsafe patterns
        if finding["ast_patterns"]["unsafe_patterns"]["direct_use"]:
            score -= 0.3
            
        if finding["ast_patterns"]["unsafe_patterns"]["missing_validation"]:
            score -= 0.2
            
        # Analyze similar patterns
        safe_patterns = sum(1 for p in finding["similar_patterns"] 
                          if p["safety_analysis"]["is_safe"])
        score += (safe_patterns / len(finding["similar_patterns"])) * 0.2
        
        # Analyze sanitizer effectiveness
        sanitizer_score = finding["sanitizer_analysis"]["sanitizer_effectiveness"]
        score += sanitizer_score * 0.1
        
        return max(0.0, min(1.0, score))
    
    def _check_input_validation(self, ast_node: dict) -> bool:
        """Check for input validation patterns"""
        # Look for validation method calls
        validation_methods = {"validate", "sanitize", "escape", "clean"}
        return any(self._find_method_calls(ast_node, validation_methods))
    
    def _check_sanitizer_calls(self, ast_node: dict) -> bool:
        """Check for sanitizer method calls"""
        sanitizer_methods = {"prepareStatement", "createQuery", "encode"}
        return any(self._find_method_calls(ast_node, sanitizer_methods))
    
    def _check_framework_protection(self, ast_node: dict) -> bool:
        """Check for framework-provided protection"""
        # Look for framework annotations and patterns
        annotations = {"@PathVariable", "@RequestParam", "@Valid"}
        return any(anno in str(ast_node) for anno in annotations)
    
    def _check_direct_use(self, ast_node: dict) -> bool:
        """Check for direct use of dangerous methods"""
        dangerous_patterns = {
            "executeQuery(",
            "execute(",
            ".decode(",
            "eval("
        }
        return any(pattern in str(ast_node) for pattern in dangerous_patterns)
    
    def _check_missing_validation(self, ast_node: dict) -> bool:
        """Check for missing validation before use"""
        # Complex logic to detect validation gaps
        return False  # Simplified for example
    
    def _check_weak_sanitization(self, ast_node: dict) -> bool:
        """Check for weak sanitization patterns"""
        weak_patterns = {
            "split(",
            "replace(",
            "substring("
        }
        return any(pattern in str(ast_node) for pattern in weak_patterns)
    
    def _analyze_pattern_safety(self, code: str) -> dict:
        """Analyze if a code pattern is safe"""
        # Vector similarity search for known safe/unsafe patterns
        return {"is_safe": True}  # Simplified for example
    
    def _find_framework_sanitizers(self, context: FindingContext) -> List[str]:
        """Find framework-provided sanitizers"""
        framework_sanitizers = []
        # Implementation to find framework sanitizers
        return framework_sanitizers
    
    def _find_custom_sanitizers(self, context: FindingContext) -> List[str]:
        """Find custom sanitizer methods"""
        custom_sanitizers = []
        # Implementation to find custom sanitizers
        return custom_sanitizers
    
    def _analyze_sanitizer_effectiveness(self, context: FindingContext) -> float:
        """Analyze effectiveness of found sanitizers"""
        return 0.5  # Simplified for example

# Example usage
if __name__ == "__main__":
    vector_db = VectorCodebaseStore()  # Initialize with codebase
    codeql_db = CodeQLDatabase()       # Initialize with CodeQL database
    
    agent = CodeQLTriageAgent(vector_db, codeql_db)
    
    # Analyze SARIF results
    results = await agent.analyze_sarif(Path("results.sarif"))
    
    # Process results
    for finding_id, confidence in results.items():
        if confidence < 0.3:
            print(f"Likely true positive: {finding_id} (confidence: {confidence:.2f})")
        elif confidence > 0.7:
            print(f"Likely false positive: {finding_id} (confidence: {confidence:.2f})")
        else:
            print(f"Needs manual review: {finding_id} (confidence: {confidence:.2f})")

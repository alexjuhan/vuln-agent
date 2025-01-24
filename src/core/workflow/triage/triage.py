'''
Triage is the process of analyzing the results of the CodeQL analysis and determining the severity of the issues found.

Steps:
1. Get the SARIF file results object
2. For each vulnerability finding, determine the severity of the issue
  - Severity
  - Potential impact
  - Exploitability
  - Confidence / false positive likelihood
3. Pattern recognition
  - Based on the vulnerabilities we've reviewed so far, what common patterns or security gaps do you notice in the codebase?
  - Enhance the existing threat model based on your analysis
4. Prioritization request:
  - Given all the vulnerabilities we've analyzed, please create a prioritized remediation plan considering:
    1. Severity of each issue
    2. Complexity of exploitation
    3. Business impact
    4. Dependencies between fixes
    5. Required effort for remediation
'''

import json
from typing import Dict, List, Optional
from prefect import task
from ...llm import get_llm_client

@task
def analyze_sarif_results(sarif_path: str) -> Optional[Dict]:
    """
    Analyze the SARIF file results using LLM to assess vulnerabilities.
    
    Args:
        sarif_path (str): Path to the SARIF output file
        
    Returns:
        Optional[Dict]: Analysis results including severity assessments and recommendations
    """
    print("\n=== Starting LLM-based Vulnerability Triage ===")
    
    try:
        # Load SARIF data
        with open(sarif_path, 'r') as f:
            sarif_data = json.load(f)
        
        llm = get_llm_client()
        
        # Prepare the context for the LLM
        vulnerability_context = _prepare_vulnerability_context(sarif_data)
        
        # Step 1: Severity Analysis
        severity_prompt = f"""Analyze these security findings and determine their severity:
        {vulnerability_context}
        
        For each vulnerability, provide:
        1. Severity rating (Critical/High/Medium/Low)
        2. Potential impact assessment
        3. Exploitability evaluation
        4. Confidence level and false positive likelihood
        
        Format your response as a JSON object."""
        
        severity_analysis = llm.analyze(severity_prompt)
        
        # Step 2: Pattern Recognition
        pattern_prompt = f"""Based on these security findings:
        {vulnerability_context}
        
        Identify:
        1. Common security patterns or gaps in the codebase
        2. Potential architectural weaknesses
        3. Recommendations for the threat model
        
        Format your response as a JSON object."""
        
        pattern_analysis = llm.analyze(pattern_prompt)
        
        # Step 3: Remediation Planning
        remediation_prompt = f"""Given these vulnerabilities and patterns:
        Severity Analysis: {severity_analysis}
        Pattern Analysis: {pattern_analysis}
        
        Create a prioritized remediation plan considering:
        1. Severity of each issue
        2. Complexity of exploitation
        3. Business impact
        4. Dependencies between fixes
        5. Required effort for remediation
        
        Format your response as a JSON object."""
        
        remediation_plan = llm.analyze(remediation_prompt)
        
        return {
            'severity_analysis': severity_analysis,
            'pattern_analysis': pattern_analysis,
            'remediation_plan': remediation_plan
        }
        
    except FileNotFoundError:
        print(f"SARIF file not found at: {sarif_path}")
        return None
    except json.JSONDecodeError:
        print(f"Error parsing SARIF file: Invalid JSON format")
        return None
    except Exception as e:
        print(f"Unexpected error during triage: {str(e)}")
        return None

def _prepare_vulnerability_context(sarif_data: Dict) -> str:
    """
    Prepare a structured context from SARIF data for LLM analysis.
    
    Args:
        sarif_data (Dict): The parsed SARIF JSON data
        
    Returns:
        str: Formatted context string for LLM prompting
    """
    context = []
    
    for run in sarif_data.get('runs', []):
        results = run.get('results', [])
        rules = {rule['id']: rule for rule in run.get('tool', {}).get('driver', {}).get('rules', [])}
        
        for result in results:
            rule_id = result.get('ruleId', 'unknown')
            rule = rules.get(rule_id, {})
            
            finding = {
                'rule_id': rule_id,
                'description': result.get('message', {}).get('text', ''),
                'category': rule.get('properties', {}).get('tags', []),
                'location': result.get('locations', [{}])[0].get('physicalLocation', {}).get('artifactLocation', {}).get('uri', 'unknown'),
                'rule_metadata': rule.get('properties', {})
            }
            
            context.append(finding)
    
    return json.dumps(context, indent=2)
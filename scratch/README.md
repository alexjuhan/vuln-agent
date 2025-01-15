# CodeQL Triage Agent

An intelligent agent that analyzes CodeQL SARIF outputs to help prioritize and triage security findings by leveraging source code context and pattern analysis.

## Overview

The CodeQL Triage Agent combines static analysis results with contextual code analysis to determine the likelihood of false positives in security findings. It uses vector embeddings of the codebase to identify similar patterns and evaluate the effectiveness of existing security controls.

## Key Features

- **Contextual Analysis**: Examines source code context around each finding, including:
  - Surrounding code lines
  - Abstract Syntax Tree (AST) patterns
  - Similar code patterns across the codebase
  - Sanitization and validation mechanisms

- **Pattern Recognition**: Identifies common security patterns:
  - Input validation routines
  - Sanitizer method calls
  - Framework-provided protections
  - Potentially unsafe patterns

- **Vector Similarity Search**: Uses code embeddings to:
  - Find similar code patterns in the codebase
  - Compare against known safe/unsafe patterns
  - Evaluate consistency of security controls

- **Confidence Scoring**: Calculates a confidence score (0.0-1.0) based on:
  - Presence of validation patterns (+0.3)
  - Sanitizer usage (+0.2)
  - Framework protections (+0.2)
  - Direct use of unsafe methods (-0.3)
  - Missing validations (-0.2)
  - Similar pattern analysis (up to +0.2)
  - Sanitizer effectiveness (up to +0.1)

## Usage
```
vector_db = VectorCodebaseStore() # Initialize with codebase
codeql_db = CodeQLDatabase() # Initialize with CodeQL database
agent = CodeQLTriageAgent(vector_db, codeql_db)
results = await agent.analyze_sarif(Path("results.sarif"))

# Process results
for finding_id, confidence in results.items():
if confidence < 0.3:
print(f"Likely true positive: {finding_id}")
elif confidence > 0.7:
print(f"Likely false positive: {finding_id}")
else:
print(f"Needs manual review: {finding_id}")
```

## Requirements

- Access to the project's CodeQL database
- Vector database containing embeddings of the source code
- SARIF output file from CodeQL analysis

## How It Works

1. **Finding Analysis**:
   - Extracts source context around each finding
   - Analyzes AST patterns for security controls
   - Identifies similar code patterns
   - Evaluates sanitization effectiveness

2. **Pattern Matching**:
   - Checks for common validation methods
   - Identifies framework-provided protections
   - Detects potentially unsafe patterns
   - Analyzes sanitizer usage

3. **Confidence Calculation**:
   - Weighs various security factors
   - Considers similar pattern analysis
   - Evaluates overall sanitization effectiveness
   - Produces a final confidence score

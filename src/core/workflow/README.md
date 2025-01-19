Vuln agent workflow

Clone repo

1. Project discovery
- file tree
- dependencies
- languages
- project type
- data flow
- trust boundaries
- README.md
- security files
- output: context 

2. Vulnerability detection
- CodeQL query selection
- run CodeQL
- run dependency-check
- output: finding

3. Triage agent
- Vector search for similar code patterns
- AST analysis
- CodeQL query writer
- learning from findings

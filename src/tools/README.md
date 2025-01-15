# Security Analyzers

This directory contains the security analysis tools used by the AI Security Agent to detect vulnerabilities in source code.

## Overview

The analyzers are implemented as Docker containers that can be run independently or orchestrated together. Each analyzer implements the `BaseTool` interface and provides specialized security analysis capabilities.

## Available Analyzers

### Semgrep
- Static Analysis Security Testing (SAST)
- Custom rules in `/rules` directory
- Runs pattern matching for security vulnerabilities

### CodeQL
- Deep semantic code analysis
- Supports multiple languages
- Requires GitHub token for database downloads

### OWASP Dependency Check
- Software Composition Analysis (SCA)
- Scans dependencies for known vulnerabilities
- Maintains persistent cache for faster subsequent runs

### NPM Audit
- Node.js specific dependency scanning
- Checks package.json and package-lock.json files
- Reports known vulnerabilities in npm packages

## Architecture

### Base Tool Interface
All analyzers implement the `BaseTool` interface:
```python
class BaseTool:
    name: str
    description: str
    parameters: dict
    
    async def execute(self, kwargs) -> ToolResponse:
        raise NotImplementedError
```

### Docker Integration
- Each analyzer runs in its own container
- Containers are defined in individual Dockerfiles
- docker-compose.yml orchestrates all analyzers
- Source code is mounted read-only at `/src`

## Usage

1. Set required environment variables:
```bash
export GITHUB_TOKEN=<your-token>  # Required for CodeQL
export ANALYZER_CACHE=/path/to/cache  # Optional: persistent cache location
```

2. Run all analyzers:
```bash
docker-compose up
```

## Adding New Analyzers

To add a new analyzer:

1. Create a new directory for the analyzer
2. Implement the `BaseTool` interface
3. Create a Dockerfile
4. Add service to docker-compose.yml
5. Add any custom rules or configurations

## Network & Storage

- All analyzers run on the `security_net` bridge network
- Persistent volume for Dependency Check cache
- Read-only source code mounting for security
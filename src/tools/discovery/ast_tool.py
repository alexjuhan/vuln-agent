from smolagents import Tool
from typing import Dict, Any
from pathlib import Path
import ast

class CodeAnalyzerTool(Tool):
    name = "code_analyzer"
    description = "Analyzes project structure, entry points, and data flows"
    

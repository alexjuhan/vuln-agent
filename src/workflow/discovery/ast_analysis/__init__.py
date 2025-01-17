from pathlib import Path
from typing import Dict
import ast

from .analyzers.flask_analyzer import FlaskAnalyzer
from .patterns.flask_patterns import TRUST_BOUNDARIES
from .models import TrustBoundary
from .utils import find_python_files

def analyze_project(project_root: str) -> dict:
    """Main function to analyze a Python project."""
    analyzer = FlaskAnalyzer()
    
    # Find and analyze Python files
    python_files = find_python_files(project_root)
    
    for path in python_files:
        try:
            with open(path, 'r', encoding='utf-8') as f:
                tree = ast.parse(f.read())
                analyzer.visit(tree)
                
                # Add main files as entry points
                if path.name == '__main__.py':
                    analyzer.entry_points.add(str(path))
        except Exception as e:
            print(f"Error processing {path}: {e}")
    
    # Convert trust boundary patterns to TrustBoundary objects
    trust_boundaries = {
        name: TrustBoundary(**boundary)
        for name, boundary in TRUST_BOUNDARIES.items()
    }
    
    return {
        'entry_points': list(analyzer.entry_points),
        'data_flows': [vars(df) for df in analyzer.data_flows],
        'trust_boundaries': {
            name: vars(boundary) 
            for name, boundary in trust_boundaries.items()
        }
    } 
import ast
import os
from dataclasses import dataclass
from typing import Dict, List, Set, Optional
from pathlib import Path

@dataclass
class DataFlow:
    source: str
    sink: str
    path: List[str]
    variables_involved: Set[str]

@dataclass
class TrustBoundary:
    name: str
    entry_points: Set[str]
    exit_points: Set[str]
    sanitizers: Set[str]

class ProjectAnalyzer(ast.NodeVisitor):
    def __init__(self):
        self.entry_points = set()
        self.data_flows = []
        self.trust_boundaries = {}
        self.current_function = None
        self.variable_sources = {}
        self.current_scope_variables = {}
        self.sanitizers = set()
        # Define source patterns (was missing before)
        self.source_patterns = {
            'request.form', 'request.args', 'request.get_json', 
            'request.data', 'request.values', 'request.files',
            'request.headers', 'request.cookies', 'request.environ'
        }
        # Update Flask patterns
        self.flask_patterns = {
            'sources': self.source_patterns,  # Reference the same patterns
            'sinks': {
                'make_response', 'jsonify', 'render_template', 
                'send_file', 'send_from_directory', 'Response', 
                'redirect', 'abort', 'stream_with_context'
            },
            'processors': {
                'before_request', 'after_request', 
                'before_first_request', 'teardown_request',
                'preprocess_request', 'process_response'
            }
        }
        
    def find_entry_points(self, root_dir: str) -> Set[str]:
        """Identify potential entry points in the project."""
        for root, _, files in os.walk(root_dir):
            # More strict test file filtering
            if any(x in root.lower() for x in ['test', 'example', 'sample']):
                continue
            
            for file in files:
                # Skip test and example files
                if file.endswith('.py') and not any(x in file.lower() for x in ['test', 'example']):
                    path = Path(root) / file
                    try:
                        with open(path, 'r', encoding='utf-8') as f:
                            content = f.read()
                            tree = ast.parse(content)
                            self.visit(tree)
                            
                            # Only add main files as entry points
                            if file == '__main__.py':
                                self.entry_points.add(str(path))
                            if 'if __name__ == "__main__"' in content:
                                self.entry_points.add(str(path))
                    except Exception as e:
                        print(f"Error processing {path}: {e}")
        
        return self.entry_points

    def visit_FunctionDef(self, node: ast.FunctionDef):
        """Track Flask route handlers and middleware."""
        prev_function = self.current_function
        self.current_function = node.name
        
        # Check for route decorators
        for decorator in node.decorator_list:
            if isinstance(decorator, ast.Call):
                if hasattr(decorator.func, 'attr') and decorator.func.attr in ['route', 'get', 'post', 'put', 'delete']:
                    self.entry_points.add(f"{self.current_function} (HTTP endpoint)")
                    # Add data flow for route handler
                    self.data_flows.append(
                        DataFlow(
                            source=f"HTTP::{self.current_function}",
                            sink=self.current_function,
                            path=["wsgi_app", "dispatch_request", self.current_function],
                            variables_involved={"request"}
                        )
                    )

        # Track middleware and request processors
        if self.current_function in self.flask_patterns['processors']:
            self.data_flows.append(
                DataFlow(
                    source=f"request::{self.current_function}",
                    sink=f"response::{self.current_function}",
                    path=["wsgi_app", self.current_function],
                    variables_involved={"request", "response"}
                )
            )

        self.generic_visit(node)
        self.current_function = prev_function

    def visit_Assign(self, node: ast.Assign):
        """Track variable assignments."""
        for target in node.targets:
            if isinstance(target, ast.Name):
                # Track the variable in current scope
                self.current_scope_variables[target.id] = {
                    'source': self.current_function,
                    'value': node.value
                }
                
                # If the value is a call to a source function, track it
                if isinstance(node.value, ast.Call) and isinstance(node.value.func, ast.Name):
                    if node.value.func.id in ['input', 'request.get_json', 'read', 'recv']:
                        self.variable_sources[target.id] = {
                            'type': 'external_input',
                            'location': self.current_function
                        }
        
        self.generic_visit(node)

    def visit_Attribute(self, node: ast.Attribute):
        """Track Flask request object attribute access."""
        if isinstance(node.value, ast.Name):
            if node.value.id == 'request':
                attr_path = f'request.{node.attr}'
                if attr_path in self.source_patterns:
                    self.variable_sources[self.current_function] = {
                        'type': 'flask_input',
                        'location': self.current_function
                    }
        self.generic_visit(node)

    def visit_Call(self, node: ast.Call):
        """Track data flows between request sources and response sinks."""
        if isinstance(node.func, ast.Attribute):
            if isinstance(node.func.value, ast.Name):
                # Track request data access
                attr_path = f"{node.func.value.id}.{node.func.attr}"
                if attr_path in self.source_patterns:
                    if self.current_function:
                        source_name = f"{self.current_function}::{attr_path}"
                        self.variable_sources[self.current_function] = {
                            'type': 'request_data',
                            'location': source_name
                        }
                        # Add data flow for request data access
                        self.data_flows.append(
                            DataFlow(
                                source=source_name,
                                sink=self.current_function,
                                path=[attr_path, self.current_function],
                                variables_involved={node.func.value.id}
                            )
                        )
                
                # Track response creation with source tracking
                elif node.func.attr in self.flask_patterns['sinks']:
                    if self.current_function:
                        source = (self.variable_sources.get(self.current_function, {})
                                .get('location', self.current_function))
                        self.data_flows.append(
                            DataFlow(
                                source=source,
                                sink=f"{self.current_function}::{node.func.attr}",
                                path=[self.current_function],
                                variables_involved=set(self.current_scope_variables.keys())
                            )
                        )

        self.generic_visit(node)

    def identify_trust_boundaries(self) -> Dict[str, TrustBoundary]:
        """Identify trust boundaries in Flask application."""
        boundaries = {}
        
        # WSGI boundary
        boundaries['wsgi'] = TrustBoundary(
            name="WSGI Boundary",
            entry_points={"wsgi_app"},
            exit_points={"__call__"},
            sanitizers=set()
        )
        
        # Request processing boundary
        boundaries['request_processing'] = TrustBoundary(
            name="Request Processing",
            entry_points=set(self.flask_patterns['processors']),
            exit_points=set(self.flask_patterns['sinks']),
            sanitizers={'escape', 'safe_join', 'secure_filename'}
        )
        
        # Session boundary
        boundaries['session'] = TrustBoundary(
            name="Session Boundary",
            entry_points={'session'},
            exit_points={'session.save'},
            sanitizers={'session.sign', 'session.encrypt'}
        )
        
        return boundaries

def analyze_project(project_root: str) -> dict:
    """Main function to analyze a Python project."""
    analyzer = ProjectAnalyzer()
    
    # Find entry points
    entry_points = analyzer.find_entry_points(project_root)
    
    # Analyze data flows and trust boundaries
    trust_boundaries = analyzer.identify_trust_boundaries()
    
    return {
        'entry_points': list(entry_points),
        'data_flows': [vars(df) for df in analyzer.data_flows],
        'trust_boundaries': {
            name: vars(boundary) 
            for name, boundary in trust_boundaries.items()
        }
    }

# Example usage
if __name__ == "__main__":
    project_path = "flask"
    analysis_results = analyze_project(project_path)
    
    print("\nEntry Points:")
    for ep in analysis_results['entry_points']:
        print(f"- {ep}")
        
    print("\nData Flows:")
    for df in analysis_results['data_flows']:
        print(f"- From {df['source']} to {df['sink']}")
        print(f"  Variables: {df['variables_involved']}")
        
    print("\nTrust Boundaries:")
    for name, boundary in analysis_results['trust_boundaries'].items():
        print(f"\nBoundary: {name}")
        print(f"Entry points: {boundary['entry_points']}")
        print(f"Exit points: {boundary['exit_points']}")
        print(f"Sanitizers: {boundary['sanitizers']}")
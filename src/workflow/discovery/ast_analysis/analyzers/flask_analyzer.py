import ast
from .base import BaseAnalyzer
from ..patterns.flask_patterns import SOURCE_PATTERNS, SINK_PATTERNS, PROCESSOR_PATTERNS
from ..models import DataFlow

class FlaskAnalyzer(BaseAnalyzer):
    def visit_FunctionDef(self, node: ast.FunctionDef):
        """Handle Flask-specific function analysis"""
        super().visit_FunctionDef(node)
        
        # Check for route decorators
        for decorator in node.decorator_list:
            if isinstance(decorator, ast.Call):
                if hasattr(decorator.func, 'attr') and decorator.func.attr in ['route', 'get', 'post', 'put', 'delete']:
                    self._handle_route_decorator(node)

        # Track middleware and request processors
        if self.current_function in PROCESSOR_PATTERNS:
            self.data_flows.append(
                DataFlow(
                    source=f"request::{self.current_function}",
                    sink=f"response::{self.current_function}",
                    path=["wsgi_app", self.current_function],
                    variables_involved={"request", "response"}
                )
            )

    def _handle_route_decorator(self, node):
        """Handle Flask route decorator analysis"""
        self.entry_points.add(f"{self.current_function} (HTTP endpoint)")
        self.data_flows.append(
            DataFlow(
                source=f"HTTP::{self.current_function}",
                sink=self.current_function,
                path=["wsgi_app", "dispatch_request", self.current_function],
                variables_involved={"request"}
            )
        )

    def visit_Assign(self, node: ast.Assign):
        """Track variable assignments"""
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
        """Track Flask request object attribute access"""
        if isinstance(node.value, ast.Name):
            if node.value.id == 'request':
                attr_path = f'request.{node.attr}'
                if attr_path in SOURCE_PATTERNS:
                    self.variable_sources[self.current_function] = {
                        'type': 'flask_input',
                        'location': self.current_function
                    }
        self.generic_visit(node)

    def visit_Call(self, node: ast.Call):
        """Track data flows between request sources and response sinks"""
        if isinstance(node.func, ast.Attribute):
            if isinstance(node.func.value, ast.Name):
                # Track request data access
                attr_path = f"{node.func.value.id}.{node.func.attr}"
                if attr_path in SOURCE_PATTERNS:
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
                elif node.func.attr in SINK_PATTERNS:
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
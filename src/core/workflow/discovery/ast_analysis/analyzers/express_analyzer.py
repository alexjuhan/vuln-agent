import ast
from typing import Dict, Any, Optional
from .base import BaseAnalyzer
from ..models import DataFlow

# Common Express.js patterns
SOURCE_PATTERNS = {
    'req.body',
    'req.query',
    'req.params',
    'req.cookies',
    'req.headers',
    'req.files'
}

SINK_PATTERNS = {
    'res.send',
    'res.json',
    'res.render',
    'res.redirect',
    'res.sendFile'
}

PROCESSOR_PATTERNS = {
    'app.use',
    'router.use',
    'express.static',
    'express.json',
    'express.urlencoded'
}

class ExpressAnalyzer(BaseAnalyzer):
    def __init__(self):
        super().__init__()
        print("[DEBUG] Initializing ExpressAnalyzer")
        self.current_route = None
        
    def analyze(self, content: str, file_path: str):
        """Analyze Express.js/TypeScript files for routes and data flows"""
        print(f"[DEBUG] Starting Express analysis of {file_path}")
        try:
            # Basic pattern matching for Express patterns since we can't use Python's ast
            self._analyze_express_patterns(content, file_path)
            print(f"[DEBUG] Completed Express analysis of {file_path}")
            print(f"[DEBUG] Found entry points: {self.entry_points}")
            print(f"[DEBUG] Found data flows: {self.data_flows}")
        except Exception as e:
            print(f"Error analyzing {file_path}: {str(e)}")

    def _analyze_express_patterns(self, content: str, file_path: str):
        """Analyze Express patterns using regex and string matching"""
        import re
        
        # Route patterns
        route_patterns = [
            r'(app|router)\.(get|post|put|delete|patch)\s*\([\'"]([^\'"]+)[\'"]',
            r'(app|router)\.(use)\s*\([\'"]([^\'"]+)[\'"]',
            r'@(Get|Post|Put|Delete|Patch)\s*\([\'"]([^\'"]+)[\'"]'  # Decorator style routes
        ]

        # Middleware patterns
        middleware_patterns = [
            r'app\.use\s*\(([^)]+)\)',
            r'router\.use\s*\(([^)]+)\)'
        ]

        # Data flow patterns
        data_source_patterns = [
            r'req\.(body|query|params|cookies|headers)',
            r'request\.(body|query|params|cookies|headers)'
        ]

        data_sink_patterns = [
            r'res\.(json|send|render|redirect)\s*\(',
            r'response\.(json|send|render|redirect)\s*\('
        ]

        # Find routes
        for pattern in route_patterns:
            matches = re.finditer(pattern, content)
            for match in matches:
                if len(match.groups()) == 3:  # app.method(path) pattern
                    method, path = match.group(2), match.group(3)
                else:  # decorator pattern
                    method, path = match.group(1).lower(), match.group(2)
                
                route_name = f"{method.upper()} {path}"
                self.entry_points.add(f"{route_name} (HTTP endpoint)")
                self.current_route = route_name

                # Add basic data flow for the route
                self.data_flows.append(
                    DataFlow(
                        source=f"HTTP::{route_name}",
                        sink=route_name,
                        path=["express", "router", route_name],
                        variables_involved={"req", "res"}
                    )
                )

        # Find middleware
        for pattern in middleware_patterns:
            matches = re.finditer(pattern, content)
            for match in matches:
                middleware_name = match.group(1).strip()
                if middleware_name:
                    self.data_flows.append(
                        DataFlow(
                            source=f"request::{middleware_name}",
                            sink=f"response::{middleware_name}",
                            path=["express", "middleware", middleware_name],
                            variables_involved={"req", "res", "next"}
                        )
                    )

        # Track data flows
        if self.current_route:
            # Find data sources
            for pattern in data_source_patterns:
                matches = re.finditer(pattern, content)
                for match in matches:
                    source_type = match.group(1)
                    self.data_flows.append(
                        DataFlow(
                            source=f"request.{source_type}",
                            sink=self.current_route,
                            path=["express", "request", source_type],
                            variables_involved={f"req.{source_type}"}
                        )
                    )

            # Find data sinks
            for pattern in data_sink_patterns:
                matches = re.finditer(pattern, content)
                for match in matches:
                    sink_type = match.group(1)
                    self.data_flows.append(
                        DataFlow(
                            source=self.current_route,
                            sink=f"response.{sink_type}",
                            path=["express", "response", sink_type],
                            variables_involved={f"res.{sink_type}"}
                        )
                    )

    def visit_Call(self, node: ast.Call):
        """Handle Express route definitions and middleware"""
        if isinstance(node.func, ast.Attribute):
            if isinstance(node.func.value, ast.Name):
                # Check for route handlers (app.get, app.post, etc.)
                if node.func.attr in ['get', 'post', 'put', 'delete', 'patch']:
                    self._handle_route_handler(node)
                
                # Check for middleware registration
                elif node.func.attr == 'use':
                    self._handle_middleware(node)

        self.generic_visit(node)

    def _handle_route_handler(self, node: ast.Call):
        """Process Express route handler definitions"""
        route_path = None
        if node.args:
            # First argument is typically the route path
            if isinstance(node.args[0], ast.Str):
                route_path = node.args[0].s

        if route_path:
            handler_name = f"{node.func.attr.upper()}__{route_path}"
            self.entry_points.add(f"{handler_name} (HTTP endpoint)")
            
            # Add data flow for the route handler
            self.data_flows.append(
                DataFlow(
                    source=f"HTTP::{handler_name}",
                    sink=handler_name,
                    path=["express", "router", handler_name],
                    variables_involved={"req", "res"}
                )
            )

    def _handle_middleware(self, node: ast.Call):
        """Process Express middleware registration"""
        middleware_name = "unnamed_middleware"
        if isinstance(node.args[0], ast.Name):
            middleware_name = node.args[0].id
        
        self.data_flows.append(
            DataFlow(
                source=f"request::{middleware_name}",
                sink=f"response::{middleware_name}",
                path=["express", "middleware", middleware_name],
                variables_involved={"req", "res", "next"}
            )
        )

    def visit_Assign(self, node: ast.Assign):
        """Track variable assignments, especially request data access"""
        for target in node.targets:
            if isinstance(target, ast.Name):
                # Track the variable in current scope
                self.current_scope_variables[target.id] = {
                    'source': self.current_function,
                    'value': node.value
                }
                
                # Track assignments from request sources
                if isinstance(node.value, ast.Attribute):
                    attr_path = self._get_attribute_path(node.value)
                    if attr_path in SOURCE_PATTERNS:
                        self.variable_sources[target.id] = {
                            'type': 'request_data',
                            'location': attr_path
                        }
        
        self.generic_visit(node)

    def _get_attribute_path(self, node):
        """Helper to build full attribute path (e.g., req.body)"""
        parts = []
        current = node
        while isinstance(current, ast.Attribute):
            parts.append(current.attr)
            current = current.value
        if isinstance(current, ast.Name):
            parts.append(current.id)
        return '.'.join(reversed(parts)) 
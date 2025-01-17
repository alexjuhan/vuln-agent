import ast
from typing import Dict, Set
from ..models import DataFlow

class BaseAnalyzer(ast.NodeVisitor):
    def __init__(self):
        self.entry_points: Set[str] = set()
        self.data_flows: List[DataFlow] = []
        self.current_function: str = None
        self.variable_sources: Dict[str, Dict] = {}
        self.current_scope_variables: Dict[str, Dict] = {}

    def visit_FunctionDef(self, node: ast.FunctionDef):
        """Base function definition visitor"""
        prev_function = self.current_function
        self.current_function = node.name
        self.generic_visit(node)
        self.current_function = prev_function 
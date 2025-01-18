import ast
from typing import Dict, Set, List
from ..models import DataFlow

class BaseAnalyzer(ast.NodeVisitor):
    def __init__(self):
        self.entry_points: Set[str] = set()
        self.data_flows: List[DataFlow] = []
        self.current_function: str = None
        self.variable_sources: Dict[str, Dict] = {}
        self.current_scope_variables: Dict[str, Dict] = {}

    @property
    def scope_variables(self) -> Set[str]:
        """Get all variables tracked across all scopes"""
        return set(self.current_scope_variables.keys())

    def analyze(self, content: str, file_path: str):
        """Base analyze method that parses and visits the AST"""
        try:
            tree = ast.parse(content)
            self.visit(tree)
        except SyntaxError as e:
            print(f"Syntax error in {file_path}: {str(e)}")
        except Exception as e:
            print(f"Error analyzing {file_path}: {str(e)}")

    def visit_FunctionDef(self, node: ast.FunctionDef):
        """Base function definition visitor"""
        prev_function = self.current_function
        self.current_function = node.name
        self.generic_visit(node)
        self.current_function = prev_function 
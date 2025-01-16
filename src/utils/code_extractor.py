import ast
from pathlib import Path
from typing import List
from src.tools.vector_store import CodeSnippet

class CodeExtractor:
    @staticmethod
    async def extract_snippets(root_dir: str) -> List[CodeSnippet]:
        snippets = []
        for path in Path(root_dir).rglob("*.py"):
            with open(path, "r") as f:
                content = f.read()
            
            try:
                tree = ast.parse(content)
                for node in ast.walk(tree):
                    if isinstance(node, (ast.FunctionDef, ast.ClassDef)):
                        snippet = CodeSnippet(
                            content=ast.get_source_segment(content, node),
                            file_path=str(path),
                            start_line=node.lineno,
                            end_line=node.end_lineno
                        )
                        snippets.append(snippet)
            except SyntaxError:
                continue
                
        return snippets 
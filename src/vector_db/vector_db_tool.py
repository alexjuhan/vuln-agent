from src.tools.base.base_tool import BaseTool
from src.tools.vector_db.vector_store import CodeVectorDB, CodeSnippet
from typing import List

class VectorDBTool(BaseTool):
    name = "vector_db"
    description = "Tool for finding similar code patterns in the codebase"
    
    def __init__(self):
        self.db = CodeVectorDB()
        
    async def index_codebase(self, code_snippets: List[CodeSnippet]):
        """Index code snippets from the codebase"""
        self.db.add_code(code_snippets)
        
    async def execute(self, query: str, **kwargs) -> List[CodeSnippet]:
        """Find similar code snippets"""
        return await self.db.query_similar_code(query) 
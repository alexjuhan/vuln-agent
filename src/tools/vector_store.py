from typing import List, Dict
import faiss
import numpy as np
from sentence_transformers import SentenceTransformer
from dataclasses import dataclass

@dataclass
class CodeSnippet:
    content: str
    file_path: str
    start_line: int
    end_line: int

class CodeVectorDB:
    def __init__(self, model_name: str = "microsoft/codebert-base"):
        self.model = SentenceTransformer(model_name)
        self.dimension = self.model.get_sentence_embedding_dimension()
        self.index = faiss.IndexFlatL2(self.dimension)
        self.snippets: List[CodeSnippet] = []
        
    def add_code(self, snippets: List[CodeSnippet]) -> None:
        """Add code snippets to the vector database"""
        if not snippets:
            return
            
        embeddings = self.model.encode([s.content for s in snippets])
        self.index.add(np.array(embeddings).astype('float32'))
        self.snippets.extend(snippets)
        
    async def query_similar_code(self, query: str, k: int = 3) -> List[CodeSnippet]:
        """Find similar code snippets for the given query"""
        query_vector = self.model.encode([query])
        distances, indices = self.index.search(
            np.array(query_vector).astype('float32'), 
            k
        )
        
        return [self.snippets[i] for i in indices[0]] 
from typing import List, Dict, Tuple
from NL2PLN.utils.ragclass import RAG
from NL2PLN.utils.common import create_openai_completion

class TypeSimilarityHandler:
    """Handles storage and comparison of type definitions"""
    
    def __init__(self, collection_name: str = "type_definitions"):
        """Initialize with a separate RAG collection for types"""
        self.rag = RAG(collection_name=collection_name)
        
    def extract_type_name(self, typedef: str) -> str:
        """Extract the type name from a typedef statement
        Example: (: Person EntityType) -> Person
        """
        try:
            # Remove outer parentheses and split
            parts = typedef.strip('()').split()
            if parts[0] == ':' and len(parts) >= 3:
                return parts[1]
        except:
            pass
        return None

    def find_similar_types(self, type_name: str, limit: int = 5) -> List[Dict]:
        """Find similar type names in the database"""
        return self.rag.search_similar(type_name, limit=limit)

    def __init__(self, collection_name: str = "type_definitions"):
        """Initialize with a separate RAG collection for types"""
        self.rag = RAG(collection_name=collection_name)
        from .dspy_type_analyzer import optimize_prompt
        self.analyzer = optimize_prompt()
        
    def analyze_type_similarities(self, new_types: List[str], similar_types: List[Dict]) -> List[str]:
        """Use DSPy-optimized prompt to analyze type similarities"""
        if not new_types:
            return []
            
        # Get full type definitions from similar types
        similar_type_defs = [t['full_type'] for t in similar_types]
        
        # Use DSPy analyzer
        statements = self.analyzer(new_types=new_types, similar_types=similar_type_defs)
        
        # Filter and return valid statements
        return [s.strip() for s in statements if s.strip()]

    def store_type(self, type_name: str, full_type: str):
        """Store a new type definition"""
        self.rag.store_embedding({
            "type_name": type_name,
            "full_type": full_type,
        }, ["type_name"])

    def process_new_typedefs(self, typedefs: List[str]) -> List[str]:
        """Process a list of new type definitions
        Returns: (linking_statements)
        """
        all_linking_statements = []
        
        # Extract all type names first
        type_names = []
        for typedef in typedefs:
            type_name = self.extract_type_name(typedef)
            if type_name:
                type_names.append(type_name)
                self.store_type(type_name, typedef)

        print(f"Extracted type names: {type_names}")
        
        # Find similar types for all new types together
        all_similar_types = []
        for type_name in type_names:
            similar_types = self.find_similar_types(type_name)
            all_similar_types.extend(similar_types)
        
        # Remove duplicates while preserving order
        seen = set()
        unique_similar_types = []
        for t in all_similar_types:
            if t['type_name'] not in seen:
                seen.add(t['type_name'])
                unique_similar_types.append(t)

        print(f"Found similar types: {unique_similar_types}")
        
        # Analyze all types together
        if type_names:
            linking_statements = self.analyze_type_similarities(type_names, unique_similar_types)
            all_linking_statements.extend(linking_statements)
                
        return all_linking_statements

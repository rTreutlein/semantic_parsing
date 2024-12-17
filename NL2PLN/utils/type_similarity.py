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

    def analyze_type_similarities(self, new_type: str, similar_types: List[Dict]) -> List[str]:
        """Use LLM to analyze similarities between types and generate linking statements"""
        if not similar_types:
            return []
            
        system_msg = [{
            "type": "text",
            "text": (
                "You are a logical reasoning expert. Analyze the similarities between types "
                "and suggest logical statements that link them. Focus on inheritance, "
                "equivalence, subset relationships, and action relationships.\n\n"
                "Example of action relationship:\n"
                "Type 1: (: LeaveSomething (-> Object Object Type))\n"
                "Type 2: (: Take (-> Object Object Type))\n"
                "Relationship: (: LeaveSomethingToTake (-> (: $l (LeaveSomething $a $b)) (Not (Take $a $b))))\n\n"
                "Return only valid MeTTa statements."
            ),
            "cache_control": {"type": "ephemeral"}
        }]
        
        user_msg = [{
            "role": "user",
            "content": (
                f"New type: {new_type}\n"
                f"Similar existing types:\n"
                f"{[t['type_name'] for t in similar_types]}\n\n"
                "Generate logical statements linking these types if appropriate. "
                "Only generate statements if there are clear logical relationships. "
                "Use standard logical predicates like Inheritance, Similarity, etc."
            )
        }]

        response = create_openai_completion(system_msg, user_msg)
        # Parse response to extract MeTTa statements
        # This would need proper parsing logic
        return [line.strip() for line in response.split('\n') if line.strip()]

    def store_type(self, type_name: str):
        """Store a new type definition"""
        self.rag.store_embedding({
            "type_name": type_name,
        }, ["type_name"])

    def process_new_typedefs(self, typedefs: List[str]) -> List[str]:
        """Process a list of new type definitions
        Returns: (linking_statements)
        """
        all_linking_statements = []
        
        for typedef in typedefs:
            type_name = self.extract_type_name(typedef)
            if type_name:
                similar_types = self.find_similar_types(type_name)
                linking_statements = self.analyze_type_similarities(type_name, similar_types)
                all_linking_statements.extend(linking_statements)
            self.store_type(typedef)
                
        return all_linking_statements

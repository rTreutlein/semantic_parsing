from typing import List, Dict
from NL2PLN.utils.ragclass import RAG
from .dspy_type_analyzer import TypeAnalyzer
from .verifier import VerifiedPredictor
from .checker import human_verify_prediction

class TypeSimilarityHandler:
    """Manages type definitions, storage, comparison, and analysis using RAG and DSPy."""
    
    def __init__(self, collection_name: str = "type_definitions", reset_db: bool = False):
        self.rag = RAG(collection_name=collection_name,reset_db=reset_db)
        analyzer = TypeAnalyzer()
        analyzer.load("claude_mipro.json")
        
        self.analyzer = VerifiedPredictor(
            predictor=analyzer,
            verify_func=human_verify_prediction,
            cache_file="verified_type_analysis_cache.json"
        )
    
    def extract_type_name(self, typedef: str) -> str | None:
        """Extract type name from definition (e.g., "(: Person EntityType)" -> "Person")"""
        try:
            parts = typedef.strip('()').split()
            return parts[1] if parts[0] == ':' and len(parts) >= 3 else None
        except:
            return None


    def analyze_type_similarities(self, new_types: List[str], similar_types: List[str]) -> List[str]:
        """Analyze similarities between new and existing types.
        
        Args:
            new_types: List of full type definitions for new types
            similar_types: List of full type definitions for similar existing types
        """
        if not new_types:
            return []
            
        prediction = self.analyzer.predict(new_types=new_types, similar_types=similar_types)
        return [s.strip() for s in prediction.statements if s.strip()]

    def process_new_typedefs(self, typedefs: List[str]) -> List[str]:
        """Process new type definitions and return linking statements."""
        # Extract type names
        type_names = []
        type_mapping = {}  # Store mapping of names to full typedefs
        for typedef in typedefs:
            if type_name := self.extract_type_name(typedef):
                type_names.append(type_name)
                type_mapping[type_name] = typedef
        
        if not type_names:
            return []

        print(f"Extracted type names: {type_names}")
        
        # Find and deduplicate similar types before storing new ones
        seen = set()
        unique_similar_types = []
        
        # Search for similar types for each type name
        for type_name in type_names:
            similar_types = self.rag.search_similar(type_name, limit=5)
            
            # Add only unseen types to results
            for type_info in similar_types:
                if type_info['type_name'] not in seen:
                    seen.add(type_info['type_name'])
                    unique_similar_types.append(type_info)

        # Store new types after finding similar ones
        for type_name, typedef in type_mapping.items():
            self.rag.store_embedding({"type_name": type_name, "full_type": typedef}, ["type_name"])

        print(f"Found similar types: {unique_similar_types}")
        
        # Pass full type definitions instead of just names
        new_type_defs = list(type_mapping.values())
        similar_type_defs = [t['full_type'] for t in unique_similar_types]
        return self.analyze_type_similarities(new_type_defs, similar_type_defs)

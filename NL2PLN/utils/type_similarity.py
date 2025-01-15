from typing import List, Dict, Any
from NL2PLN.utils.ragclass import RAG
from .dspy_type_analyzer import TypeAnalyzer
from .verifier import VerifiedPredictor

class TypeSimilarityHandler:
    """Manages type definitions, storage, comparison, and analysis using RAG and DSPy."""
    
    def __init__(self, collection_name: str = "type_definitions"):
        self.rag = RAG(collection_name=collection_name)
        analyzer = TypeAnalyzer()
        analyzer.load("claude_optimized_type_analyzer2.json")
        
        def verify_analysis(prediction, input_data):
            # Simple pass-through verification for now
            # Could be enhanced with specific verification logic
            return prediction
            
        self.analyzer = VerifiedPredictor(
            predictor=analyzer,
            verify_func=verify_analysis,
            cache_file="verified_type_analysis_cache.json"
        )
    
    def extract_type_name(self, typedef: str) -> str | None:
        """Extract type name from definition (e.g., "(: Person EntityType)" -> "Person")"""
        try:
            parts = typedef.strip('()').split()
            return parts[1] if parts[0] == ':' and len(parts) >= 3 else None
        except:
            return None


    def analyze_type_similarities(self, new_types: List[str], similar_types: List[Dict]) -> List[str]:
        """Analyze similarities between new and existing types."""
        if not new_types:
            return []
            
        similar_type_defs = [t['full_type'] for t in similar_types]
        prediction = self.analyzer.predict(new_types=new_types, similar_types=similar_type_defs)
        return [s.strip() for s in prediction.statements if s.strip()]

    def process_new_typedefs(self, typedefs: List[str]) -> List[str]:
        """Process new type definitions and return linking statements."""
        # Extract and store types
        type_names = []
        for typedef in typedefs:
            if type_name := self.extract_type_name(typedef):
                type_names.append(type_name)
                self.rag.store_embedding({"type_name": type_name, "full_type": typedef}, ["type_name"])
        
        if not type_names:
            return []

        print(f"Extracted type names: {type_names}")
        
        # Find and deduplicate similar types
        seen = set()
        unique_similar_types = [
            t for types in (self.rag.search_similar(name, limit=5) for name in type_names)
            for t in types if t['type_name'] not in seen and not seen.add(t['type_name'])
        ]

        print(f"Found similar types: {unique_similar_types}")
        
        return self.analyze_type_similarities(type_names, unique_similar_types)

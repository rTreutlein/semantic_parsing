import json
import os
from typing import List, Dict, Any
from NL2PLN.utils.ragclass import RAG
from .dspy_type_analyzer import TypeAnalyzer

class TypeSimilarityHandler:
    """Manages type definitions, storage, comparison, and analysis using RAG and DSPy."""
    
    def __init__(self, collection_name: str = "type_definitions", cache_file: str = "analyzer_cache.json"):
        self.rag = RAG(collection_name=collection_name)
        self.analyzer = TypeAnalyzer()
        self.analyzer.load("claude_optimized_type_analyzer2.json")
        self.cache_file = cache_file
        self.cache = self._load_cache()
        
    def _load_cache(self) -> Dict:
        if not os.path.exists(self.cache_file):
            return {}
        try:
            with open(self.cache_file, 'r') as f:
                return json.load(f)
        except json.JSONDecodeError:
            return {}
    
    def _save_cache(self):
        with open(self.cache_file, 'w') as f:
            json.dump(self.cache, f, indent=2)
    
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
        analysis_signature = str({"new_types": sorted(new_types), "similar_types": sorted(similar_type_defs)})
        
        if analysis_signature in self.cache:
            return [s.strip() for s in self.cache[analysis_signature] if s.strip()]
        
        prediction = self.analyzer(new_types=new_types, similar_types=similar_type_defs)
        self.cache[analysis_signature] = prediction.statements
        self._save_cache()
        
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

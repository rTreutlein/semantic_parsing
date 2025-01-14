import json
import os
from typing import List, Dict, Any
from NL2PLN.utils.ragclass import RAG
from .dspy_type_analyzer import TypeAnalyzer

class TypeSimilarityHandler:
    """Manages type definitions, storage, comparison, and analysis using RAG and DSPy."""
    
    def __init__(self, collection_name: str = "type_definitions", cache_file: str = "analyzer_cache.json"):
        """Initialize the handler with RAG collection and cache settings.
        
        Args:
            collection_name: Name of the RAG collection for storing types
            cache_file: Path to the JSON file for caching analyzer results
        """
        """Initialize with a separate RAG collection for types"""
        self.rag = RAG(collection_name=collection_name)
        self.analyzer = TypeAnalyzer()
        self.analyzer.load("claude_optimized_type_analyzer2.json")
        self.cache_file = cache_file
        self.cache = self._load_cache()
        
    # Cache Management Methods
    # ----------------------
    
    def _load_cache(self) -> Dict:
        """Load the analyzer cache from file if it exists."""
        if os.path.exists(self.cache_file):
            try:
                with open(self.cache_file, 'r') as f:
                    return json.load(f)
            except json.JSONDecodeError:
                return {}
        return {}
    
    def _save_cache(self):
        """Save the current analyzer cache to file."""
        with open(self.cache_file, 'w') as f:
            json.dump(self.cache, f, indent=2)
        
    # Type Definition Processing Methods
    # --------------------------------
    
    def extract_type_name(self, typedef: str) -> str | None:
        """Extract the type name from a typedef statement.
        
        Args:
            typedef: Type definition string (e.g., "(: Person EntityType)")
        
        Returns:
            The extracted type name or None if parsing fails
        
        Example:
            "(: Person EntityType)" -> "Person"
        """
        try:
            parts = typedef.strip('()').split()
            if parts[0] == ':' and len(parts) >= 3:
                return parts[1]
        except:
            pass
        return None


    def analyze_type_similarities(self, new_types: List[str], similar_types: List[Dict]) -> List[str]:
        """Analyze similarities between new types and existing types.
        
        Uses DSPy-optimized prompt to analyze type similarities, with caching
        to avoid redundant analysis.
        
        Args:
            new_types: List of new type names to analyze
            similar_types: List of dictionaries containing similar type information
            
        Returns:
            List of similarity statements
        """
        if not new_types:
            return []
            
        # Get full type definitions from similar types
        similar_type_defs = [t['full_type'] for t in similar_types]
        
        # Create a unique signature for this analysis
        # Sort to ensure same types in different order create same signature
        analysis_signature = str({
            "new_types": sorted(new_types),
            "similar_types": sorted(similar_type_defs)
        })
        
        # Check if we have this analysis cached
        if analysis_signature in self.cache:
            return [s.strip() for s in self.cache[analysis_signature] if s.strip()]
        
        # If not found, perform new analysis
        prediction = self.analyzer(new_types=new_types, similar_types=similar_type_defs)
        
        # Store in cache
        self.cache[analysis_signature] = prediction.statements
        self._save_cache()
        
        # Filter and return valid statements
        return [s.strip() for s in prediction.statements if s.strip()]

    # Main Processing Pipeline
    # ----------------------

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

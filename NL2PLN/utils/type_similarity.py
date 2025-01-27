from typing import List, Dict
from NL2PLN.utils.ragclass import RAG
from .dspy_type_analyzer import TypeAnalyzer
from .verifier import VerifiedPredictor
from .checker import human_verify_prediction

class TypeSimilarityHandler:
    """Manages type definitions, storage, comparison, and analysis using RAG and DSPy."""
    
    def __init__(self, collection_name: str = "type_definitions", reset_db: bool = False, verify: bool = False):
        self.rag = RAG(collection_name=collection_name,reset_db=reset_db)
        self.analyzer = TypeAnalyzer()
        self.analyzer.load("claude_mipro.json")
        self.pending_types = []  # Store staged type definitions
        
        if verify:
            self.analyzer = VerifiedPredictor(
                predictor=self.analyzer,
                verify_func=human_verify_prediction,
                cache_file="verified_type_analysis_cache.json",
                verify_kwargs=["new_types", "similar_types"],
            )
    
    def extract_type_name(self, typedef: str) -> str | None:
        """Extract type name from definition (e.g., "(: Person EntityType)" -> "Person")"""
        try:
            parts = typedef.strip('()').split()
            return parts[1] if parts[0] == ':' and len(parts) >= 3 else None
        except:
            return None

    @staticmethod
    def balance_parentheses(expr: str) -> str:
        """Balance parentheses in an expression by adding or removing at the end."""
        # Add opening parenthesis if expression starts with colon
        if expr.startswith(':'):
            expr = '(' + expr
            
        open_count = expr.count('(')
        close_count = expr.count(')')
        
        if open_count > close_count:
            # Add missing closing parentheses
            return expr + ')' * (open_count - close_count)
        elif close_count > open_count:
            # Remove only excess closing parentheses from the end
            excess = close_count - open_count
            i = len(expr) - 1
            
            # First verify the end of string contains only closing parentheses
            while i >= 0 and excess > 0:
                if expr[i] != ')':
                    # Found non-parenthesis - give up and return original
                    return expr
                i -= 1
                excess -= 1
                
            # If we got here, we found enough closing parentheses at the end
            # Now remove the exact number of excess ones
            excess = close_count - open_count
            return expr[:-excess]
        return expr

    def analyze_type_similarities(self, new_types: List[str], similar_types: List[str]) -> List[str]:
        """Analyze similarities between new and existing types.
        
        Args:
            new_types: List of full type definitions for new types
            similar_types: List of full type definitions for similar existing types
        """
        if not new_types:
            return []

        print(f"Analyzing similarities between\n{new_types}\nand\n{similar_types}")
            
        prediction = self.analyzer(new_types=new_types, similar_types=similar_types)

        return [self.balance_parentheses(x.strip()) for x in prediction.statements]

    def stage_new_typedefs(self, typedefs: List[str]) -> List[str]:
        """Stage new type definitions without committing them and return linking statements."""
        # Extract type names
        type_names = []
        type_mapping = {}  # Store mapping of names to full typedefs
        for typedef in typedefs:
            if type_name := self.extract_type_name(typedef):
                type_names.append(type_name)
                type_mapping[type_name] = typedef
        
        if not type_names:
            return []

        # Find and deduplicate similar types
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

        # Stage new types for later commitment
        self.pending_types.extend(list(type_mapping.values()))

        # Pass full type definitions including both staged and existing types
        new_type_defs = list(type_mapping.values())
        similar_type_defs = [t['full_type'] for t in unique_similar_types]
        # Include pending types in similarity analysis
        all_similar_types = similar_type_defs + self.pending_types
        return self.analyze_type_similarities(new_type_defs, all_similar_types)

    def commit_pending_types(self):
        """Commit staged types to RAG database."""
        for typedef in self.pending_types:
            if type_name := self.extract_type_name(typedef):
                self.rag.store_embedding({"type_name": type_name, "full_type": typedef}, ["type_name"])
        self.pending_types.clear()

    def clear_pending_types(self):
        """Discard all staged types."""
        self.pending_types.clear()

    def process_new_typedefs(self, typedefs: List[str]) -> List[str]:
        """Legacy method that immediately commits types. Use stage_new_typedefs instead."""
        linking_statements = self.stage_new_typedefs(typedefs)
        self.commit_pending_types()
        return linking_statements

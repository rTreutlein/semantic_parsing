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

    def analyze_type_similarities(self, new_types: List[str], similar_types: List[Dict]) -> List[str]:
        """Use LLM to analyze similarities between types and generate linking statements"""
        if not new_types:
            return []
            
        system_msg = [{
            "type": "text",
            "text": (
                "You are a logical reasoning expert. Analyze the similarities between types "
                "and suggest logical statements that link them using dependent type theory.\n\n"
                "Use only these type operators:\n"
                "* -> for functions/dependent products (Π types)\n"
                "* Not for negation (from Type to Type)\n\n"
                
                "Examples of relationships:\n"
                "1. Simple inheritance:\n"
                "Type 1: (: Apple (-> Object Type))\n"
                "Type 2: (: Fruit (-> Object Type))\n"
                "Relationship: (: AppleIsFruit (-> (: $a (Apple $a)) (Fruit $a)))\n\n"

                "2. Action negation:\n"
                "Type 1: (: LeaveSomething (-> Object Object Type))\n"
                "Type 2: (: Take (-> Object Object Type))\n"
                "Relationship: (: LeaveSomethingToTake (-> (: $l (LeaveSomething $a $b)) (Not (Take $a $b))))\n\n"

                "3. Curried functions:\n"
                "Input;"
                "Type 1: (: Vehicle (-> Object Type))\n"
                "Type 2: (: Red (-> Object Type))\n"
                "Type 3: (: RedVehicle (-> Object Type))\n"
                "Output:"
                "```"
                "(: ToRedVehicle (-> (Vehicle $x) (-> (Red $x) (RedVehicle $x))))\n\n"
                "```"

                "Try to think of a counter example before suggesting a relationship.\n"
                "Don't invent new Types use only the ones provided.\n"
                "Only create Relations which are always true. If something is only possible ignore it.\n"
                "Return only valid MeTTa statements.\n"
                "The Final Output should be surrounded by triple backticks (```) and consist of one statement per line."
                "It is fine to return nothing."
            ),
            "cache_control": {"type": "ephemeral"}
        }]
        
        user_msg = [{
            "role": "user",
            "content": (
                f"New types:\n{new_types}\n\n"
                f"Similar existing types:\n"
                f"{[t['type_name'] for t in similar_types]}\n\n"
                f"Generate logical statements linking the new types to each other and "
                f"to the existing types where appropriate."
            )
        }]

        response = create_openai_completion(system_msg, user_msg)

        print(response)
        
        # Extract content between triple backticks
        if '```' in response:
            parts = response.split('```')
            if len(parts) >= 2:
                # Get the content between first set of backticks
                statements = parts[1].strip().split('\n')
                # Filter empty lines and strip whitespace
                return [line.strip() for line in statements if line.strip()]
        
        return []

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
        
        # Extract all type names first
        type_names = []
        for typedef in typedefs:
            type_name = self.extract_type_name(typedef)
            if type_name:
                type_names.append(type_name)
                self.store_type(typedef)
        
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
        
        # Analyze all types together
        if type_names:
            linking_statements = self.analyze_type_similarities(type_names, unique_similar_types)
            all_linking_statements.extend(linking_statements)
                
        return all_linking_statements

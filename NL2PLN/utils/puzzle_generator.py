from typing import Dict, List, Tuple
from .common import create_openai_completion

class LogicPuzzleGenerator:
    """Generates logic puzzles in narrative form with their logical solutions."""
    
    def __init__(self):
        self.system_prompt = """You are a logic puzzle creator. Create puzzles following these rules:
1. Write a short story (2-3 paragraphs) that contains logical premises hidden in natural language
2. The story should be casual and natural, not obviously a logic puzzle
3. Include 3-4 clear logical premises that can lead to a conclusion
4. Provide the formal logical representation of each premise and the conclusion
5. Use only simple predicates and implications

Format your response as:
STORY:
[Your story here]

PREMISES:
1. [First premise in natural language]
2. [Second premise in natural language]
...

LOGICAL_FORM:
[Premise 1 in predicate logic]
[Premise 2 in predicate logic]
...
[Conclusion in predicate logic]"""

    def generate_puzzle(self) -> Dict[str, str]:
        """
        Generates a logical puzzle in story form with its logical solution.
        
        Returns:
            Dict containing:
                - 'story': The narrative version of the puzzle
                - 'premises': List of premises in natural language
                - 'logical_form': The formal logical representation
        """
        response = create_openai_completion(
            system_msg=self.system_prompt,
            user_msg="Generate a logic puzzle about everyday situations that can be solved using simple logical reasoning.",
            model="claude-3-5-sonnet-20241022"
        )
        
        # Parse the response into components
        sections = {}
        current_section = None
        current_content = []
        
        for line in response.split('\n'):
            if line.strip() in ['STORY:', 'PREMISES:', 'LOGICAL_FORM:']:
                if current_section:
                    sections[current_section] = '\n'.join(current_content).strip()
                current_section = line.strip()[:-1].lower()
                current_content = []
            else:
                current_content.append(line)
        
        if current_section:
            sections[current_section] = '\n'.join(current_content).strip()
            
        return sections

    def validate_puzzle(self, puzzle: Dict[str, str]) -> bool:
        """
        Validates that the generated puzzle meets our requirements.
        
        Args:
            puzzle: Dictionary containing story, premises, and logical form
            
        Returns:
            bool: True if the puzzle is valid
        """
        # Basic validation checks
        if not all(k in puzzle for k in ['story', 'premises', 'logical_form']):
            return False
            
        # Story should be substantial but not too long
        if not (50 <= len(puzzle['story'].split()) <= 200):
            return False
            
        # Should have multiple premises in logical form
        logical_statements = [s for s in puzzle['logical_form'].split('\n') if s.strip()]
        if len(logical_statements) < 3:  # At least 2 premises + 1 conclusion
            return False
            
        return True

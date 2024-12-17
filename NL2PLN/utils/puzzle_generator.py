from typing import Dict, List, Tuple
from .common import create_openai_completion

class LogicPuzzleGenerator:
    """Generates logic puzzles in narrative form with their logical solutions."""
    
    def __init__(self):
        self.system_prompt = """You are a logic puzzle creator. Create puzzles following these rules:
1. Write a short story that contains logical premises hidden in natural language
2. The story should be casual and natural, not obviously a logic puzzle
3. Split the story into Premises and Conclusion
4. Start a new line for each Sentence
5. Include common sense knowledge required to solve the puzzle

Format your response as:
Premises:
[The beginning of the story containing the premises here]

Conclusion:
[The conclusion of the story here]

Common Sense Knowledge:
[List the common sense facts needed to solve this puzzle]

Here's an example:

Premises:
John always takes his umbrella when it rains.
This morning, John left his umbrella at home.

Conclusion:
It wasn't raining this morning.

Common Sense Knowledge:
If someone always does A when B occurs, and they didn't do A, then B didn't occur
Morning is a time of day
People can choose whether to take or leave items
Umbrellas are items that can be carried
"""

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
            user_msg=[{"role": "user", "content": "Generate a logic puzzle about everyday situations that can be solved using simple logical reasoning."}],
            model="claude-3-5-sonnet-20241022"
        )
        
        # Parse the response into components
        sections = {}
        current_section = None
        current_content = []
        
        for line in response.split('\n'):
            if line.strip() in ['Premises:', 'Conclusion:']:
                if current_section:
                    sections[current_section] = '\n'.join(current_content).strip()
                current_section = line.strip()[:-1].lower()
                current_content = []
            else:
                current_content.append(line)
        
        if current_section:
            sections[current_section] = '\n'.join(current_content).strip()
            
        # Add empty string if common sense section is missing
        sections['common_sense'] = sections.get('common sense knowledge', '')
        return sections

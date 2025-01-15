from typing import Dict, List, Tuple
import dspy

class PuzzleGeneratorSignature(dspy.Signature):
    """Signature for generating logic puzzles."""
    premises = dspy.OutputField(desc="The story premises containing logical statements")
    conclusion = dspy.OutputField(desc="The logical conclusion from the premises")
    common_sense = dspy.OutputField(desc="Common sense knowledge needed to solve the puzzle")

class LogicPuzzleGenerator(dspy.Module):
    """Generates logic puzzles in narrative form with their logical solutions."""
    
    def __init__(self):
        super().__init__()
        self.generate = dspy.ChainOfThought(PuzzleGeneratorSignature)
        self.prompt = """You are a logic puzzle creator. Create puzzles following these rules:
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
                - 'premises': The story premises containing logical statements
                - 'conclusion': The logical conclusion from the premises
                - 'common_sense': Common sense knowledge needed to solve the puzzle
        """
        prediction = self.generate()
        return {
            'premises': prediction.premises,
            'conclusion': prediction.conclusion,
            'common_sense': prediction.common_sense
        }

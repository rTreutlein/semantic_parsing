from typing import Dict, List, Tuple
import dspy

#"""You are a logic puzzle creator. Create puzzles following these rules:
#1. Write a short story that contains logical premises hidden in natural language
#2. The story should be casual and natural, not obviously a logic puzzle
#3. Split the story into Premises and Conclusion
#4. Start a new line for each Sentence
#5. Include common sense knowledge required to solve the puzzle
#6. Assume we already have the absolute basics like implication and contraposition
#7. Don't number the sentences in any of the sections
#"""

class PuzzleGeneratorSignature(dspy.Signature):
    """You are a logic puzzle creator. Create puzzles following these rules:
    1. Write a short story that contains logical premises
    2. Don't number the sentences in any of the sections
    """
    numberOfPremises : int = dspy.InputField(desc="Number of premises to generate")

    premises : List[str] = dspy.OutputField(desc="The story premises containing logical statements")
    deduction : List[Tuple[list[str],str]] = dspy.OutputField(desc="The individual deduction steps consisting of the premises used and their logical conclusion")
    conclusion : str = dspy.OutputField(desc="The logical conclusion from the premises")

class LogicPuzzleGenerator(dspy.Module):
    """Generates logic puzzles in narrative form with their logical solutions."""
    
    def __init__(self):
        super().__init__()
        self.generate = dspy.ChainOfThought(PuzzleGeneratorSignature)

    def generate_puzzle(self, numberOfPremises: int = 3) -> Dict:
        """
        Generates a logical puzzle in story form with its logical solution.
        
        Returns:
            Dict containing:
                - 'premises': The story premises containing logical statements
                - 'conclusion': The logical conclusion from the premises
                - 'common_sense': Common sense knowledge needed to solve the puzzle
        """
        with dspy.context(lm=dspy.LM('anthropic/claude-3-5-sonnet-20241022',temperature=1,cache=False)):
            prediction = self.generate(numberOfPremises=numberOfPremises)
        return prediction

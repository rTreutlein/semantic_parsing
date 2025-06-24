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

class SampleGeneratorSignature(dspy.Signature):
    """You are a sample generateor.
    A sample consists of paragraph (with a specific number of sentences) and a Question whos answer is contained in the Paragraph.
    To answer the Question information from most or all of the Sentences should be required.
    But no additional information like common sense knowledge should be needed.
    """
    numberOfSentences : int = dspy.InputField(desc="Number of sentences to generate")

    sentences : List[str] = dspy.OutputField(desc="The sentences in the paragraph")
    question : str = dspy.OutputField(desc="The Question to be answerd")

class SampleGenerator(dspy.Module):
    """Generates logic puzzles in narrative form with their logical solutions."""
    
    def __init__(self):
        super().__init__()
        self.generate = dspy.ChainOfThought(SampleGeneratorSignature)

    def generate_sample(self, numberOfSentences: int = 3) -> dspy.Prediction:
        with dspy.context(lm=dspy.LM('openrouter/anthropic/claude-sonnet-4',temperature=1,cache=False)):
        #with dspy.context(lm=dspy.LM('deepseek/deepseek-reasoner',temperature=1,cache=False)):
            return self.generate(numberOfSentences=numberOfSentences)

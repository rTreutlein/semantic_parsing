from typing import Dict, List, Tuple
import dspy

class SampleGeneratorSignature(dspy.Signature):
    """You are a sample generator that creates distinct logic puzzles.
    Given some recent samples and a number of sentences, generate a new sample that:
    1. Has the requested number of sentences
    2. Contains a question answerable from the sentences
    3. Is meaningfully different from all recent samples
    4. Doesn't reuse the same logical structure or content
    """
    numberOfSentences : int = dspy.InputField(desc="Number of sentences to generate")
    recent_samples : List[str] = dspy.InputField(desc="Recent samples to avoid similarity with")

    sentences : List[str] = dspy.OutputField(desc="The sentences in the paragraph")
    question : str = dspy.OutputField(desc="The Question to be answered")

class SampleGenerator(dspy.Module):
    """Generates distinct logic puzzles in narrative form."""

    def __init__(self):
        super().__init__()
        self.generate = dspy.ChainOfThought(SampleGeneratorSignature)

    def forward(self, numberOfSentences: int = 3, recent_samples: list = None) -> dspy.Prediction:
        return self.generate_sample(numberOfSentences=numberOfSentences, recent_samples=recent_samples)

    def generate_sample(self, numberOfSentences: int = 3, recent_samples: list = None) -> dspy.Prediction:
        """Generate a sample that differs from recent_samples."""
        recent_samples = recent_samples or []
        return self.generate(
            numberOfSentences=numberOfSentences,
            recent_samples=[str(s) for s in recent_samples]
        )

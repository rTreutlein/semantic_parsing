"""
Optimize the SampleGenerator prompt so that the produced puzzles have a
medium difficulty for the current NL2PLN → proof pipeline.

A puzzle is considered of *medium* difficulty when the downstream
SimplePuzzleProcessor returns a score that is **not** 0 or 1
(0 = too hard, 1 = too easy).

The script:
1. Loads the already-optimized NL2PLN module from ``optimized.json``.
2. Uses previously stored medium-difficulty puzzles found in the
   ``puzzle`` directory as a training set.  
   Each example only supplies ``numberOfSentences`` so that the
   SampleGenerator learns to create puzzles of the desired length.
3. Runs MIPRO-v2 teleprompting to optimise the SampleGenerator prompt.
4. Saves the optimised generator back to ``sample_generator_optimized.json``.
"""
from typing import List
import argparse
import random

import dspy
from dspy.teleprompt import MIPROv2

from NL2PLN.simple_nl2pln import SimpleNL2PLN
from NL2PLN.simple_puzzle_manager import SimplePuzzleProcessor
from NL2PLN.utils.sample_generator import SampleGenerator


# --------------------------------------------------------------------------- #
#  LM configuration                                                           #
# --------------------------------------------------------------------------- #
#dspy.configure(lm=dspy.LM("openrouter/anthropic/claude-sonnet-4"))
dspy.configure(lm=dspy.LM("openai/gpt-4o"))

# --------------------------------------------------------------------------- #
#  Helper to build the training dataset                                       #
# --------------------------------------------------------------------------- #
def build_training_dataset(min_len: int, max_len: int, num_samples: int) -> List[dspy.Example]:
    """
    Create ``num_samples`` examples with sentence lengths
    uniformly sampled between ``min_len`` and ``max_len`` (inclusive).
    """
    dataset: List[dspy.Example] = []
    for _ in range(num_samples):
        length = random.randint(min_len, max_len)
        dataset.append(
            dspy.Example(numberOfSentences=length).with_inputs("numberOfSentences")
        )
    return dataset


# --------------------------------------------------------------------------- #
#  Difficulty metric                                                          #
# --------------------------------------------------------------------------- #
def difficulty_metric(example: dspy.Example, prediction: dspy.Prediction, trace=None) -> float:
    """
    Return 1.0 if the generated puzzle has *medium* difficulty, else 0.0.

    A puzzle is of medium difficulty when SimplePuzzleProcessor returns
    a score that is neither 0 (too hard) nor 1 (too easy).
    """
    nl2pln = SimpleNL2PLN()
    nl2pln.load("optimized.json")

    processor = SimplePuzzleProcessor(
        output_base="metric",
        nl2pln=nl2pln,
        verify=False,
        n=5
    )

    score = processor.process_puzzle(prediction)
    return 1.0 if score not in (0, 1) else 0.0


# --------------------------------------------------------------------------- #
#  Optimisation                                                               #
# --------------------------------------------------------------------------- #
parser = argparse.ArgumentParser(
    description="Optimize SampleGenerator to produce medium-difficulty puzzles"
)
parser.add_argument("--min-length", type=int, default=3,
                    help="Minimum number of sentences in generated puzzles")
parser.add_argument("--max-length", type=int, default=5,
                    help="Maximum number of sentences in generated puzzles")
parser.add_argument("--num-samples", type=int, default=20,
                    help="Number of training examples used during optimisation")
args = parser.parse_args()

trainset = build_training_dataset(args.min_length, args.max_length, args.num_samples)

teleprompter = MIPROv2(metric=difficulty_metric, auto="light")

generator = SampleGenerator()
print("Optimising SampleGenerator prompt …")
generator_optimised = teleprompter.compile(
    generator,
    trainset=trainset,
    requires_permission_to_run=False,
)

generator_optimised.save("sample_generator_optimized.json")
print("Optimised generator saved to sample_generator_optimized.json")

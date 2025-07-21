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
from pathlib import Path
from typing import List

import dspy
from dspy.teleprompt import MIPROv2

from NL2PLN.simple_nl2pln import SimpleNL2PLN
from NL2PLN.simple_puzzle_manager import SimplePuzzleProcessor
from NL2PLN.utils.sample_generator import SampleGenerator
from NL2PLN.simple_opt import load_medium_puzzles_dataset  # reuse helper


# --------------------------------------------------------------------------- #
#  LM configuration                                                           #
# --------------------------------------------------------------------------- #
dspy.configure(lm=dspy.LM("openrouter/anthropic/claude-sonnet-4"))


# --------------------------------------------------------------------------- #
#  Helper to build the training dataset                                       #
# --------------------------------------------------------------------------- #
def build_training_dataset(medium_puzzles_dir: str) -> List[dspy.Example]:
    """Return examples providing only the requested sentence count."""
    puzzles = load_medium_puzzles_dataset(medium_puzzles_dir)
    dataset: List[dspy.Example] = []
    for p in puzzles:
        # `sentences` is guaranteed by `load_medium_puzzles_dataset`
        dataset.append(
            dspy.Example(numberOfSentences=len(p.sentences)).with_inputs("numberOfSentences")
        )
    return dataset


# --------------------------------------------------------------------------- #
#  Difficulty metric                                                          #
# --------------------------------------------------------------------------- #
def difficulty_metric(example: dspy.Example, preds: List[dspy.Prediction], trace=None) -> float:
    """
    Score is the fraction of predictions whose puzzles are of medium difficulty
    for the current NL2PLN → proof pipeline.
    """
    # Load optimised NL2PLN once per metric call.
    nl2pln = SimpleNL2PLN()
    nl2pln.load("optimized.json")

    processor = SimplePuzzleProcessor(
        output_base="metric", nl2pln=nl2pln, verify=False, n=5
    )

    medium_hits = 0
    for prediction in preds:
        score = processor.process_puzzle(prediction)
        if score not in (0, 1):
            medium_hits += 1

    return medium_hits / len(preds) if preds else 0.0


# --------------------------------------------------------------------------- #
#  Optimisation                                                               #
# --------------------------------------------------------------------------- #
trainset = build_training_dataset("puzzle")

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

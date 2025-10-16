from typing import List
import argparse
import json
import random
import litellm

litellm.drop_params = True

import dspy
from dspy.teleprompt import GEPA

from NL2PLN.simple_module import SimpleModule , difficulty_metric

# --------------------------------------------------------------------------- #
#  LM configuration                                                           #
# --------------------------------------------------------------------------- #
#dspy.configure(lm=dspy.LM("openrouter/anthropic/claude-sonnet-4"))
#model = "openai/gpt-5"
#model = "openrouter/z-ai/glm-4.5"
model = "openrouter/openai/gpt-oss-120b"

dspy.configure(lm=dspy.LM(model,temperature=1.0, max_tokens=20000))

# --------------------------------------------------------------------------- #
#  Helper to load datasets from COCA                                          #
# --------------------------------------------------------------------------- #
def build_examples_from_file(filepath: str) -> List[dspy.Example]:
    """
    Load a JSON file containing a list of puzzle data and convert each item into a
    dspy.Example that provides 'sentences' (list[str]) and 'questions' (list[dict]) as inputs.
    """
    examples: List[dspy.Example] = []
    with open(filepath, "r", encoding="utf-8") as f:
        puzzle_data = json.load(f)
    for item in puzzle_data:
        examples.append(
            dspy.Example(sentences=item["sentences"], questions=item["queries"]).with_inputs("sentences", "questions")
        )
    return examples


# --------------------------------------------------------------------------- #
#  Optimisation                                                               #
# --------------------------------------------------------------------------- #
#parser = argparse.ArgumentParser(
#    description="Optimize SampleGenerator using COCA train/val datasets"
#)
#parser.add_argument("--train-file", type=str, default="NL2PLN/COCA/train.txt",
#                    help="Path to training text file (one sentence per line)")
#parser.add_argument("--val-file", type=str, default="NL2PLN/COCA/val.txt",
#                    help="Path to validation text file (one sentence per line)")
#args = parser.parse_args()

trainset = build_examples_from_file("sentences.json")
#valset = build_examples_from_file(args.val_file)

teleprompter = GEPA(metric=difficulty_metric
                   ,reflection_lm=dspy.LM(model="openai/gpt-5", temperature=1.0, max_tokens=32000)
                   ,num_threads=4
                   ,log_dir="gepa_log"
                   ,max_full_evals=3)

module = SimpleModule(model=model)

generator_optimised = teleprompter.compile(
    module,
    trainset=trainset,
    #valset=valset,
)

generator_optimised.save("sample_module_optimzied.json")
print("Optimised generator saved to sample_module_optimzied.json")

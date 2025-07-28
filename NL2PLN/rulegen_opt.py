"""
Script to optimise the rule-generation ChainOfThought that is used inside
SimpleModule.  We create a minimal training set with a single illustrative
example and run MIPROv2 to tune the prompt.  The optimised module is saved
to ``rulegen_optimized.json``.
"""
from __future__ import annotations

import argparse
from typing import List

import dspy
from dspy.teleprompt import MIPROv2

from NL2PLN.metta.mettalog_handler import MettalogHandler


# --------------------------------------------------------------------------- #
#  LM configuration                                                           #
# --------------------------------------------------------------------------- #
MODEL_NAME = "openai/gpt-4.1"
dspy.configure(lm=dspy.LM(MODEL_NAME, temperature=1.0, max_tokens=20000))

# --------------------------------------------------------------------------- #
#  Helper to build the (tiny) training dataset                                #
# --------------------------------------------------------------------------- #
def build_training_dataset() -> List[dspy.Example]:
    """
    Return a single illustrative example for prompt tuning.
    """
    example = dspy.Example(
        input_statements=[
            "(: human_socrates (Human Socrates) no_tv)",
        ],
        target_query="(: $prf (Mortal Socrates) $tv)",
        required_rules=[
            "(: human_implies_mortal (Implication (Human $x) (Mortal $x)) (STV 1.0 1.0))"
        ],
    ).with_inputs("input_statements", "target_query")
    return [example]


# --------------------------------------------------------------------------- #
#  Metric                                                                     #
# --------------------------------------------------------------------------- #
def pass_through_metric(example: dspy.Example,
                        prediction: dspy.Prediction,
                        trace=None) -> float:
    """
    A placeholder metric that always returns 1.0 – replace with a real metric
    once a validation mechanism is in place.
    """
    ml = MettalogHandler()
    for statement in example.input_statements:
        ml.add_atom(statement)
    for rule in prediction.required_rules:
        ml.add_atom(rule)
    proofs = ml.query(example.target_query)
    return len(proofs) > 0


# --------------------------------------------------------------------------- #
#  Main optimisation routine                                                  #
# --------------------------------------------------------------------------- #
def main() -> None:
    parser = argparse.ArgumentParser(
        description="Optimise the rule-generation ChainOfThought prompt"
    )
    parser.add_argument("--out", default="rulegen_optimized.json",
                        help="File to save the optimised module")
    args = parser.parse_args()

    trainset = build_training_dataset()

    teleprompter = MIPROv2(metric=pass_through_metric, auto="light")

    print("Optimising rule generator prompt …")
    rulegen = dspy.ChainOfThought("input_statements, target_query -> required_rules : List[str]")
    rulegen_optimised = teleprompter.compile(
        rulegen,
        trainset=trainset,
        requires_permission_to_run=False,
    )

    rulegen_optimised.save(args.out)
    print(f"Optimised rule generator saved to {args.out}")


if __name__ == "__main__":
    main()

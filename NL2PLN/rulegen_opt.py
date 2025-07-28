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


# --------------------------------------------------------------------------- #
#  LM configuration                                                           #
# --------------------------------------------------------------------------- #
MODEL_NAME = "openai/gpt-4.1"
dspy.configure(lm=dspy.LM(MODEL_NAME, temperature=1.0, max_tokens=20000))


# --------------------------------------------------------------------------- #
#  Rule-generation wrapper                                                    #
# --------------------------------------------------------------------------- #
class RuleGenModule(dspy.Module):
    """
    Thin wrapper around the ChainOfThought prompt that generates the logical
    rules needed to prove a query from a set of input statements.
    """
    def __init__(self, model: str = MODEL_NAME):
        super().__init__()
        # Signature must match the one used in SimpleModule
        self.rulegen = dspy.ChainOfThought(
            "input_statements, target_query -> required_rules : List[str]"
        )

    def forward(self, input_statements: List[str], target_query: str) -> dspy.Prediction:
        """
        Simply delegate to the underlying ChainOfThought prompt.
        """
        return self.rulegen(
            input_statements=input_statements,
            target_query=target_query,
        )


# --------------------------------------------------------------------------- #
#  Helper to build the (tiny) training dataset                                #
# --------------------------------------------------------------------------- #
def build_training_dataset() -> List[dspy.Example]:
    """
    Return a single illustrative example for prompt tuning.
    """
    example = dspy.Example(
        input_statements=[
            "(Human Socrates)",
            "(-> (Human ?x) (Mortal ?x))"
        ],
        target_query="(Mortal Socrates)",
        required_rules=[
            "(-> (Human ?x) (Mortal ?x))"
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
    return 1.0


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
    rulegen_module = RuleGenModule()
    rulegen_optimised = teleprompter.compile(
        rulegen_module,
        trainset=trainset,
        requires_permission_to_run=False,
    )

    rulegen_optimised.save(args.out)
    print(f"Optimised rule generator saved to {args.out}")


if __name__ == "__main__":
    main()

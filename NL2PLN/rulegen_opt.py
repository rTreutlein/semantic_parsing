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
from dspy.teleprompt import MIPROv2,SIMBA

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
    Return a small set of illustrative examples for prompt tuning.
    """
    examples: List[dspy.Example] = []

    # Example 1 ─ Socrates is mortal
    examples.append(
        dspy.Example(
            input_statements=[
                "(: human_socrates (Human Socrates) (STV 1.0 1.0))",
            ],
            target_query="(: $prf (Mortal Socrates) $tv)",
            required_rules=[
                "(: human_implies_mortal (Implication (Human $x) (Mortal $x)) (STV 1.0 1.0))"
            ],
        ).with_inputs("input_statements", "target_query")
    )

    # Example 2 ─ Tweety can fly
    examples.append(
        dspy.Example(
            input_statements=[
                "(: bird_tweety (Bird Tweety) (STV 1.0 1.0))",
            ],
            target_query="(: $prf (CanFly Tweety) $tv)",
            required_rules=[
                "(: birds_can_fly (Implication (Bird $x) (CanFly $x)) (STV 1.0 1.0))"
            ],
        ).with_inputs("input_statements", "target_query")
    )

    examples.append(
        dspy.Example(
            input_statements=['(: maria_finished_hw (WithTV (Finished Maria Homework MariaFinishesHomework) (STV 1.0 1.0)))', '(: sam_started_project (WithTV (Started Sam Project SamStartsProject) (STV 1.0 1.0)))', '(: temporal_relation (WithTV (Before MariaFinishesHomework SamStartsProject) (STV 1.0 1.0)))'],
            target_query="(: $query (WithTV (And (BeginsWork (WorkingOn Maria Assignment) $tMaria) (BeginsWork (WorkingOn Sam Assignment) $tSam) (LessThan $tMaria $tSam) (Equivalence $who Maria)) $tv))"
        ).with_inputs("input_statements", "target_query")
    )

    examples.append(
        dspy.Example(
            input_statements=['(: samantha_before_tom (WithTV (FinishedBefore Samantha Tom) (STV 1.0 1.0)))', '(: alex_before_samantha (WithTV (FinishedBefore Alex Samantha) (STV 1.0 1.0)))'],
            target_query='(: $query (WithTV (FinishedLast $person) $tv))'
        ).with_inputs("input_statements", "target_query")
    )



    return examples

# --------------------------------------------------------------------------- #
#  Metric                                                                     #
# --------------------------------------------------------------------------- #
def pass_through_metric(example: dspy.Example,
                        prediction: dspy.Prediction,
                        trace=None) -> bool:
    """
    A placeholder metric that always returns 1.0 – replace with a real metric
    once a validation mechanism is in place.
    """
    ml = MettalogHandler()
    for statement in example.input_statements:
        ml.add_atom(statement)
    for rule in prediction.required_rules:
        ml.add_atom(rule)
    proofs = ml.query(example.target_query,log=True)
    return len(proofs) > 0

class RulegenSignature(dspy.Signature):
    """
    You task is to generate a list of rules that are required to answer the target query given the input statements.
    Rules have the form:
    (: rule_name (Implication (Predicate1 $x) (Predicate2 $x)) (STV 1.0 1.0))
    or with conjunctions/disjunctions:
    (: rule_name (Implication (And (Predicate1 $x) (Predicate2 $x)) (Or (Predicate3 $x) (Predicate4 $x))) (STV 1.0 1.0))
    """
    input_statements : List[str] = dspy.InputField(desc="The input statements to be converted to PLN")
    target_query : str = dspy.InputField(desc="The target query to be answered")

    required_rules : List[str] = dspy.OutputField(desc="The required rules to answer the target query")


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

    #teleprompter = MIPROv2(metric=pass_through_metric, auto="light")
    teleprompter = SIMBA(metric=pass_through_metric, bsize=4)

    print("Optimising rule generator prompt …")
    rulegen = dspy.ChainOfThought(RulegenSignature)
    rulegen_optimised = teleprompter.compile(
        rulegen,
        trainset=trainset,
        #requires_permission_to_run=False,
    )

    rulegen_optimised.save(args.out)
    print(f"Optimised rule generator saved to {args.out}")

def test():
    rulegen = dspy.ChainOfThought(RulegenSignature)

    trainset = build_training_dataset()

    pred = rulegen(input_statements = trainset[0].input_statements, target_query = trainset[0].target_query)

    print(pred)

    res = pass_through_metric(trainset[0], pred)
    print(res)

if __name__ == "__main__":
    main()

    

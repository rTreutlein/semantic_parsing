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

    # Example 5 ─ John is Anna's grandparent via transitive ancestry
    examples.append(
        dspy.Example(
            input_statements=[
                "(: parent_john_mary (Parent John Mary) (STV 1.0 1.0))",
                "(: parent_mary_anna (Parent Mary Anna) (STV 1.0 1.0))",
            ],
            target_query="(: $prf (Grandparent John Anna) $tv)",
            required_rules=[
                "(: parent_implies_ancestor (Implication (Parent $x $y) (Ancestor $x $y)) (STV 1.0 1.0))",
                "(: ancestor_transitive (Implication (And (Ancestor $x $y) (Ancestor $y $z)) (Ancestor $x $z)) (STV 1.0 1.0))",
                "(: ancestor_implies_grandparent (Implication (Ancestor $x $y) (Grandparent $x $y)) (STV 1.0 1.0))",
            ],
        ).with_inputs("input_statements", "target_query")
    )

    # Example 6 ─ Squares are polygons
    examples.append(
        dspy.Example(
            input_statements=[
                "(: square_a (Square A) (STV 1.0 1.0))",
            ],
            target_query="(: $prf (Polygon A) $tv)",
            required_rules=[
                "(: square_to_rectangle (Implication (Square $x) (Rectangle $x)) (STV 1.0 1.0))",
                "(: rectangle_to_polygon (Implication (Rectangle $x) (Polygon $x)) (STV 1.0 1.0))",
            ],
        ).with_inputs("input_statements", "target_query")
    )

    # Example 7 ─ Voting eligibility from age and citizenship
    examples.append(
        dspy.Example(
            input_statements=[
                "(: age_alice_18 (Age Alice 18) (STV 1.0 1.0))",
                "(: citizen_alice (Citizen Alice) (STV 1.0 1.0))",
                "(: geq_18 (GreaterOrEqual 18 18) (STV 1.0 1.0))",
            ],
            target_query="(: $prf (EligibleToVote Alice) $tv)",
            required_rules=[
                "(: adult_def (Implication (And (Age $x $age) (GreaterOrEqual $age 18)) (Adult $x)) (STV 1.0 1.0))",
                "(: voting_rule (Implication (And (Adult $x) (Citizen $x)) (EligibleToVote $x)) (STV 1.0 1.0))",
            ],
        ).with_inputs(\"input_statements\", \"target_query\")
    )

    # Example 8 ─ Traffic-light reasoning for car movement
    examples.append(
        dspy.Example(
            input_statements=[
                "(: light1_green (TrafficLightState Light1 Green) (STV 1.0 1.0))",
                "(: car1_at_light1 (CarAt Car1 Light1) (STV 1.0 1.0))",
            ],
            target_query="(: $prf (CanGo Car1) $tv)",
            required_rules=[
                "(: green_means_go (Implication (And (TrafficLightState $l Green) (CarAt $c $l)) (CanGo $c)) (STV 1.0 1.0))",
            ],
        ).with_inputs(\"input_statements\", \"target_query\")
    )

    # Example 9 ─ Nested subset & membership inference
    examples.append(
        dspy.Example(
            input_statements=[
                "(: cats_subset_mammals (Subset Cats Mammals) (STV 1.0 1.0))",
                "(: mammals_subset_animals (Subset Mammals Animals) (STV 1.0 1.0))",
                "(: felix_cat (Member Felix Cats) (STV 1.0 1.0))",
            ],
            target_query="(: $prf (Member Felix Animals) $tv)",
            required_rules=[
                "(: subset_trans (Implication (And (Subset $A $B) (Subset $B $C)) (Subset $A $C)) (STV 1.0 1.0))",
                "(: member_subset (Implication (And (Member $x $A) (Subset $A $B)) (Member $x $B)) (STV 1.0 1.0))",
            ],
        ).with_inputs(\"input_statements\", \"target_query\")
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
    proofs = ml.query(example.target_query)
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
    """Run the rule generator on every example in the training set and
    print whether a proof was found for each."""
    rulegen = dspy.ChainOfThought(RulegenSignature)
    rulegen.load("rulegen_optimized.json")
    trainset = build_training_dataset()

    for idx, example in enumerate(trainset, start=1):
        pred = rulegen(
            input_statements=example.input_statements,
            target_query=example.target_query,
        )
        print(f"\nExample {idx} prediction:")
        print(pred)

        success = pass_through_metric(example, pred)
        print(f"Proof found: {success}")

if __name__ == "__main__":
    #main()
    test()


    

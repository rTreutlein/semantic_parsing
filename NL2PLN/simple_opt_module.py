from typing import List
import argparse
import random
import litellm

litellm.drop_params = True

import dspy
from dspy.teleprompt import GEPA

from NL2PLN.simple_module import SimpleModule

# --------------------------------------------------------------------------- #
#  LM configuration                                                           #
# --------------------------------------------------------------------------- #
#dspy.configure(lm=dspy.LM("openrouter/anthropic/claude-sonnet-4"))
#model = "openai/gpt-5"
#model = "openrouter/z-ai/glm-4.5"
model = "openrouter/google/gemini-2.5-flash-lite"

dspy.configure(lm=dspy.LM(model,temperature=1.0, max_tokens=20000))

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
            dspy.Example(num_sentences=length).with_inputs("num_sentences")
        )
    return dataset


# --------------------------------------------------------------------------- #
#  Difficulty metric                                                          #
# --------------------------------------------------------------------------- #
def difficulty_metric(gold: dspy.Example, pred: dspy.Prediction, trace=None):
    metta_handler = MettalogHandler()
    compare : dspy.Module = dspy.ChainOfThought("question, expected_answer, found_proof -> proof_matches_expected_answer : bool")

    for stmt in prediction.stmts:
        if checkStmt(stmt) == 0.0:
            print(f"Statement {stmt} is not valid")
            metta_handler.close()
            return dspy.Prediction(score=False, feedback="One of the pln statements did not follow the right syntax it should look like (: proof_name (Predicate x) (STV strength confidence))")
        metta_handler.add_atom(stmt)

    for rule in rules.required_rules:
        if checkStmt(rule) == 0.0:
            print(f"Rule {rule} is not valid")
            metta_handler.close()
            return dspy.Prediction(score=False, feedback="One of the pln rules did not follow the right syntax it should look like (: proof_name (Implication (PredicateA x) (PredicateB x)) (STV strength confidence))")
        metta_handler.add_atom(rule)

    for query in prediction.queries:
        if checkQuery(query) == 0.0:
            print(f"Query {query} is not valid")
            metta_handler.close()
            return dspy.Prediction(score=False, feedback="One of the pln queries did not follow the right syntax it should look like (: $prf (Predicate x) $tv)")

    proofs = []
    for query in pln_query.questions:
        query_res = metta_handler.query(query)
        for res in query_res:
            if res.startswith("(query"):
                print(f"Query not executed")
                continue
            else:
                proofs.append(res)

    comparison = compare(question=pred.question, expected_answer=pred.expected_answer, found_proof=proofs)

    metta_handler.close()

    return dspy.Prediction(score=comparison.proof_matches_expected_answer, feedback=comparison.reasoning)



# --------------------------------------------------------------------------- #
#  Optimisation                                                               #
# --------------------------------------------------------------------------- #
parser = argparse.ArgumentParser(
    description="Optimize SampleGenerator to produce medium-difficulty puzzles"
)
parser.add_argument("--min-length", type=int, default=3,
                    help="Minimum number of sentences in generated puzzles")
parser.add_argument("--max-length", type=int, default=10,
                    help="Maximum number of sentences in generated puzzles")
parser.add_argument("--num-samples", type=int, default=2,
                    help="Number of training examples used during optimisation")
args = parser.parse_args()

trainset = build_training_dataset(args.min_length, args.max_length, args.num_samples)

teleprompter = GEPA(metric=difficulty_metric
                   ,reflection_lm=dspy.LM(model="openai/gpt-5", temperature=1.0, max_tokens=32000)
                   ,num_threads=8
                   ,log_dir="gepa_log"
                   ,auto="light")

module = SimpleModule(model=model)

generator_optimised = teleprompter.compile(
    module,
    trainset=trainset,
)

generator_optimised.save("sample_module_optimzied.json")
print("Optimised generator saved to sample_module_optimzied.json")

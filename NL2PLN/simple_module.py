import datetime
import dspy
import json
import logging
from typing import List

import textwrap
from concurrent.futures import ThreadPoolExecutor
from dspy.adapters.utils import get_field_description_string

logger = logging.getLogger(__name__)
from NL2PLN.simple_nl2pln import SimpleNL2PLN
#from NL2PLN.metta.mettalog_handler import MettalogHandler
from NL2PLN.utils.sample_generator import SampleGenerator
from NL2PLN.utils.cleanPLN import checkStmt, checkQuery, checkImpl, balance_parentheses

import sys
sys.path.append("/nexus/Dev/OpenCog/MM2Chainer/")

from mork_handler import MorkHandler

class RulegenSignature(dspy.Signature):
    """
    You task is to generate a list of rules that are required to answer the target query given the input statements.
    Rules have the form:
    (: rule_name (Implication (Predicate1 $x) (Predicate2 $x)) (STV 1.0 1.0))
    or with conjunctions/disjunctions:
    (: rule_name (Implication (And (Predicate1 $x) (Predicate2 $x)) (Or (Predicate3 $x) (Predicate4 $x))) (STV 1.0 1.0))

    Example:
    input_statement:
    (: mas_is_dog (Dog max) (STV 1.0 1.0))
    target_query:
    (: $max_is_what_animal (Animal max $type) $tv)

    required_rules:
    (: dog_to_animal_type (Implication (Dog $d) (Animal $d dog)) (STV 1.0 1.0))
    """
    input_statements : List[str] = dspy.InputField(desc="The input statements to be converted to PLN")
    target_query : str = dspy.InputField(desc="The target query to be answered")

    required_rules : List[str] = dspy.OutputField(desc="The required rules to answer the target query")

class NL2PLNLSig(dspy.Signature):
    """
    Convert the input english to PLN Light.
    Format:
    (: prf statment truth_value)

    prf should be either a specific name for this proof or a variable $prf for queries
    statment can range from a simple (Predicate obj) to complex (Implicaiton (And (Predicate1 $x) (Predicate2 $x)) (Or (Predicate3 $x) (Predicate4 $x)))
    or anything in between. For quereis we can also have varaiables in the place of any other element like ($pred obj) or ($connection (Predicate1 $x) (Predicate2 $x))

    truth_value have the shape of (STV strenght confidence) where strenght and confidence are floats between 0 and 1.
    again for quereis they should usualy just be a variable $tv

    Example:
    English: Max is a Dog
    PLN Light: (: max_is_dog (Dog max) (STV 1.0 1.0))

    English: Is Max a Dog?
    PLN Light: (: $max_is_dog_prf (Dog max) $tv)

    English: All dogs chase a cat.
    PLN Light: (: dogs_chase_cat (Implication (Dog $dog) (And (Cat $cat) (Chase $dog $cat))) (STV 1.0 1.0)) 
    Note: Unbound varaibles in the conclusion of an Implication like above are automatically excistantially quantified.
          Universal Quantification/Forall is represented by Implication

    """
    english : str = dspy.InputField(desc="The input sentences to be converted to PLN Light")

    plnl : List[str] = dspy.OutputField(desc="The converted PLN Light")


class SimpleModule(dspy.Module):
    def __init__(self, model: str = "openai/gpt-4o"):
        self.model : str = model
        self.nl2pln : dspy.Module = dspy.ChainOfThought(NL2PLNLSig)
        self.rulegen : dspy.Module = dspy.ChainOfThought(RulegenSignature)

    def forward(self, sentences : List[str], questions: List[dict]):
        stmts = self.nl2pln(english=sentences).plnl

        queries_pln = []
        rules_list = []
        for q in questions:
            pln_q = self.nl2pln(english=q['question']).plnl
            queries_pln.extend(pln_q)
            rules = self.rulegen(input_statements=stmts, target_query=pln_q[0] if pln_q else "")
            rules_list.extend(rules.required_rules)

        return dspy.Prediction(stmts=stmts, queries=queries_pln, rules=rules_list, questions=questions)

def run_io_tasks_in_parallel(tasks):
    with ThreadPoolExecutor() as executor:
        running_tasks = [executor.submit(task) for task in tasks]
        for running_task in running_tasks:
            running_task.result()

def extract_rule_name(rule: str) -> str:
    """Extract the rule name from a PLN rule string, e.g., 'extract_any_from_and' from '(: extract_any_from_and ...'."""
    parts = rule.strip().split()
    if len(parts) >= 2 and parts[0] == '(:':
        return parts[1]
    return ""

def difficulty_metric(gold: dspy.Example, pred: dspy.Prediction, trace=None, pred_name=None, pred_trace=None):
    metta_handler = MorkHandler()
    compare : dspy.Module = dspy.ChainOfThought("question, expected_answer, found_proof -> proof_matches_expected_answer : bool")
    validate_rule : dspy.Module = dspy.ChainOfThought("statement, rule -> is_valid : bool")

    penalty = 0
    penalty_reason = ""

    for stmt in pred.stmts:
        stmt , score = balance_parentheses(stmt)
        if checkStmt(stmt) == 0.0:
            print(f"Statement {stmt} is not valid")
            return dspy.Prediction(score=0.0, feedback="One of the pln statements did not follow the right syntax it should look like (: proof_name (Predicate x) (STV strength confidence))")
        print("Adding statement: " + stmt)
        metta_handler.add_atom(stmt)

    for rule in pred.rules:
        rule , score = balance_parentheses(rule)
        if checkImpl(rule) == 0.0:
            print(f"Rule {rule} is not valid")
            return dspy.Prediction(score=0.0, feedback="One of the pln rules did not follow the right syntax it should look like (: proof_name (Implication (PredicateA x) (PredicateB x)) (STV strength confidence))")
        if not validate_rule(statement=stmt, rule=rule).is_valid:
            print(f"Rule {rule} is not valid")
            return dspy.Prediction(score=0.0, feedback=f"This rule is not logicaly sound: {rule}")
        print("Adding rule: " + rule)
        metta_handler.add_atom(rule)

    correct_matches = 0
    total_questions = len(pred.questions)
    feedback_details = []
    for i, query in enumerate(pred.queries):
        query , score = balance_parentheses(query)
        if checkQuery(query) == 0.0:
            print(f"Query {query} is not valid")
            return dspy.Prediction(score=0.0, feedback="One of the pln queries did not follow the right syntax it should look like (: $prf (Predicate x) $tv)")

    proofs = []
    for query in pred.queries:
        query , _ = balance_parentheses(query)
        query_res = metta_handler.query(query)
        proofs.append(query_res)

    # Check if generated rules were used in the proofs
    used_rules = set()
    for proof in proofs:
        proof_str = str(proof)  # Convert to string to handle lists or nested structures
        for rule in pred.rules:
            name = extract_rule_name(rule)
            if name and name in proof_str:
                used_rules.add(name)

    total_rules = len(pred.rules)
    used_count = len(used_rules)
    unused_count = total_rules - used_count
    penalty = unused_count * 0.01  # Penalty of 0.01 per unused rule
    score = max(0.0, score - penalty)  # Cap score at 0

    # Compare each question's proof against its expected answer
    for i, q in enumerate(pred.questions):
        if i < len(proofs):
            comparison = compare(question=q['question'], expected_answer=q['expected_answer'], found_proof=proofs[i])
            print(comparison.reasoning)
            if comparison.proof_matches_expected_answer:
                correct_matches += 1
                feedback_details.append(f"Positive: Question '{q['question']}' matched expected answer. Reasoning: {comparison.reasoning}")
            else:
                feedback_details.append(f"Negative: Question '{q['question']}' did not match expected answer. Reasoning: {comparison.reasoning}")
        else:
            feedback_details.append(f"Negative: No proof found for question '{q['question']}'.")

    unused_rules = [rule for rule in pred.rules if extract_rule_name(rule) not in used_rules]
    score = correct_matches / total_questions if total_questions > 0 else 0.0
    score = max(0.0, score - penalty)  # Apply penalty again if needed (though already applied above)
    rule_feedback = f"Rules used: {used_count}/{total_rules}. Unused rules: {unused_rules}. Penalty applied: {penalty}."
    detailed_feedback = f"Score: {correct_matches}/{total_questions} questions matched. {rule_feedback}\n" + "\n".join(feedback_details)
    return dspy.Prediction(score=score, feedback=detailed_feedback)

if __name__ == '__main__':
    #model = "openrouter/google/gemini-2.5-flash-lite"
    #model = "openai/gpt-4o" #{'openai/gpt-4o': {'completion_tokens': 1217, 'prompt_tokens': 5139, 'total_tokens': 6356, 'completion_tokens_details': {'accepted_prediction_tokens': 0, 'audio_tokens': 0, 'reasoning_tokens': 0, 'rejected_prediction_tokens': 0, 'text_tokens': 0}, 'prompt_tokens_details': {'audio_tokens': 0, 'cached_tokens': 1536, 'text_tokens': 0, 'image_tokens': 0}}}
    #model = "openai/o3" #{'openai/o3': {'completion_tokens': 6834, 'prompt_tokens': 5279, 'total_tokens': 12113, 'completion_tokens_details': {'accepted_prediction_tokens': 0, 'audio_tokens': 0, 'reasoning_tokens': 5376, 'rejected_prediction_tokens': 0, 'text_tokens': 0}, 'prompt_tokens_details': {'audio_tokens': 0, 'cached_tokens': 1536, 'text_tokens': 0, 'image_tokens': 0}}}
    #model = "openai/gpt-4.1"
    #model = "openrouter/qwen/qwen3-235b-a22b-thinking-2507"
    #model = "openrouter/z-ai/glm-4.5"
    model = "openrouter/openai/gpt-oss-120b"

    #print(inspect.getsource(SimpleModule))


    dspy.configure(lm=dspy.LM(model,temperature=1.0, max_tokens=20000))
    dspy.settings.configure(track_usage=True)

    module = SimpleModule(model=model)
    module.load("sample_module_optimzied.json")

    # Load and parse tmp.pzl
    with open("sentences.json", "r") as f:
        puzzle_data = json.load(f)
    sentences = puzzle_data[2]["sentences"]
    questions = puzzle_data[2]["queries"]

    res = module(sentences=sentences, questions=questions)
    print(res)
    metric = difficulty_metric("empty", res)
    print(metric)

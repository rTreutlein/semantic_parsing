import datetime
import dspy
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
        self.questiongen : dspy.Module = dspy.ChainOfThought("text -> question , expected_answer")
        self.nl2pln : dspy.Module = dspy.ChainOfThought(NL2PLNLSig)
        self.rulegen : dspy.Module = dspy.ChainOfThought(RulegenSignature)

    def forward(self, sentences : List[str], queries):
        #tmp = self.questiongen(text=sentences)
        #question = tmp.question
        #expected_answer = tmp.expected_answer

        stmts = self.nl2pln(english=sentences).plnl

        qureies_pln
        for query in queries:
            pln_query = self.nl2pln(english=query.question).plnl
            rules = self.rulegen(input_statements=stmts, target_query=pln_query)

        return dspy.Prediction(stmts=stmts, queries=queries, rules=rules.required_rules,question=question, expected_answer=expected_answer)

def run_io_tasks_in_parallel(tasks):
    with ThreadPoolExecutor() as executor:
        running_tasks = [executor.submit(task) for task in tasks]
        for running_task in running_tasks:
            running_task.result()

def difficulty_metric(gold: dspy.Example, pred: dspy.Prediction, trace=None, pred_name=None, pred_trace=None):
    metta_handler = MorkHandler()
    compare : dspy.Module = dspy.ChainOfThought("question, expected_answer, found_proof -> proof_matches_expected_answer : bool")

    penalty = 0
    peanlty_reason = ""

    for stmt in pred.stmts:
        stmt , score = balance_parentheses(stmt)
        if checkStmt(stmt) == 0.0:
            print(f"Statement {stmt} is not valid")
            return dspy.Prediction(score=False, feedback="One of the pln statements did not follow the right syntax it should look like (: proof_name (Predicate x) (STV strength confidence))")
        metta_handler.add_atom(stmt)

    for rule in pred.rules:
        rule , score = balance_parentheses(rule)
        if checkImpl(rule) == 0.0:
            print(f"Rule {rule} is not valid")
            return dspy.Prediction(score=False, feedback="One of the pln rules did not follow the right syntax it should look like (: proof_name (Implication (PredicateA x) (PredicateB x)) (STV strength confidence))")
        metta_handler.add_atom(rule)

    for query in pred.queries:
        query , score = balance_parentheses(query)
        if checkQuery(query) == 0.0:
            print(f"Query {query} is not valid")
            return dspy.Prediction(score=False, feedback="One of the pln queries did not follow the right syntax it should look like (: $prf (Predicate x) $tv)")

    proofs = []
    try:
        for query in pred.queries:
            query , score = balance_parentheses(query)
            query_res = metta_handler.query(query)
            for res in query_res:
                if res.startswith("(query"):
                    print(f"Query not executed")
                    continue
                else:
                    proofs.append(res)
    except TimeoutError:
        return dspy.Prediction(score=False, feedback="The proof timedout")

    comparison = compare(question=pred.question, expected_answer=pred.expected_answer, found_proof=proofs)

    return dspy.Prediction(score=comparison.proof_matches_expected_answer, feedback=comparison.reasoning)



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

    res = module(sentences=["10.10.2025, Bob went swimming today"],question="11.10.2025, What was Bob doing yesterday?",expected_answer="Bob was swimming")
    print(res)
    metric = difficulty_metric("empty", res)
    print(metric)

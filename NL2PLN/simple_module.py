import datetime
import dspy
import json
import logging
from typing import List

import textwrap
from textwrap import dedent
from concurrent.futures import ThreadPoolExecutor
from dspy.adapters.utils import get_field_description_string

logger = logging.getLogger(__name__)
from NL2PLN.simple_nl2pln import SimpleNL2PLN
#from NL2PLN.metta.mettalog_handler import MettalogHandler
from NL2PLN.utils.sample_generator import SampleGenerator
from NL2PLN.utils.cleanPLN import checkStmt, checkQuery, checkImpl, balance_parentheses

import sys
sys.path.append("../../OpenCog/MM2Chainer/")

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

    Make sure that the rules generated are logically valid. Do not just generate a rule from input to output if it makes no sense.
    If it's not possilbe to reach the target query using generaly valid rules then return nothing

    Example of rephrasing:
    (: take_to_taking (Implication (Take $x $y) (Taking $x $y)) (STV 1.0 1.0))

    Example of negation:
    (: take_to_not_leave (Implication (Take $x $y) (Not (Leave $x $y))) (STV 1.0 1.0))
    (: take_to_not_leave (Implication (Take $x $y) (Leave $x $y)) (STV 0.0 1.0))
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

    Make sure to use a granual representation so it will be easy to answer a variaty of question about the sentence:
    English: The Dog has brown fur.
    BAD: 
    (: dog_has_brown_fur (Has dog brown_fur) (STV 1.0 1.0))

    GOOD:
    (: dog (Dog dog) (STV 1.0 1.0))
    (: has (Has dog fur) (STV 1.0 1.0))
    (: fur (Fur fur) (STV 1.0 1.0))
    (: brown_fur (Color brown fur) (STV 1.0 1.0))

    When translating natural language to logic, certain words carry meanings that differ from their literal interpretation due to common usage. These words often express quantifiers, modalities, or degrees of frequency/intensity that require careful handling to capture their intended meaning.
    These words are stuff like "always", "never", "frequently", "sometimes", "often", "rarely", "very", "extremely", "a lot", "a little", "some", "many", "few", "fewer", "more", "most"
    when possilbe enocde their meing in the TruthValue.
    For example:
    English: The dog is sometimes happy.
    (: dog (Dog dog) (STV 1.0 1.0))
    (: dog_happy (Happy dog) (STV 0.1 0.7))
    So probablity of 0.1 with condifdenc 0.7 so basically the do is happy 10% of the time.

    Or alternatively: 
    English: The dog is always running.
    (: dog (Dog dog) (STV 1.0 1.0))
    (: dog_running (Running dog) (STV 0.5 1.0))
    The dog can't literally always run all the time.

    Take care that for question the prf and the tv should be variables (starting with $)

    The above examples are just that examples of a possible solution. Before you generate your answer. Pick a probabilty between 0 and 1.
    That describing how likely your answer is.
    """
    english : str = dspy.InputField(desc="The input sentences to be converted to PLN Light")

    plnl : List[str] = dspy.OutputField(desc="The converted PLN Light")

class SimpleModule(dspy.Module):
    def __init__(self, model: str = "openai/gpt-4o"):
        self.model : str = model
        self.nl2pln : dspy.Module = dspy.ChainOfThought(NL2PLNLSig)
        self.rulegen : dspy.Module = dspy.ChainOfThought(RulegenSignature)

    def forward(self, sentences : List[str], queries: List[dict]):
        stmts = self.nl2pln(english=sentences).plnl

        queries_pln = []
        for q in queries:
            pln_q = self.nl2pln(english=q['question']).plnl
            #if pln_q is None or len(pln_q) != 1:
            #raise Exception("NL2PLN returned more than one query: " + str(pln_q))
            rules = self.rulegen(input_statements=stmts, target_query=pln_q[0]).required_rules
            queries_pln.append({'query': pln_q[0],'rules': rules})

        return dspy.Prediction(statements=stmts, queries=queries_pln)

def extract_rule_name(rule: str) -> str:
    """Extract the rule name from a PLN rule string, e.g., 'extract_any_from_and' from '(: extract_any_from_and ...'."""
    parts = rule.strip().split()
    if len(parts) >= 2 and parts[0] == '(:':
        return parts[1]
    return ""

class ValidateRuleSig(dspy.Signature):
    """
    Validate a rule to make sure it is logically valid.
    These rules are not knowledge but are generated to map between differnt represenations.
    So they should be obvioulsy true in any context.
    This includes renaming/repharsing things so:
    (: take_to_taking (Implication (Take $x $y) (Taking $x $y)) (STV 1.0 1.0))
    is fine also:
    (: take_to_not_leave (Implication (Take $x $y) (Not (Leave $x $y))) (STV 1.0 1.0))
    or encoded as:
    (: take_to_not_leave (Implication (Take $x $y) (Leave $x $y)) (STV 0.0 1.0))
    """
    rule : str = dspy.InputField(desc="The rule to be validated")
    is_logically_valid : bool = dspy.OutputField(desc="True if the rule is logically valid, False otherwise")

class CompareResultSig(dspy.Signature):
    """
    Compare the expected answer to the found proof.
    The proof will have the shape (: proof_path (Proofen Statment) (STV strenght confidence))
    strenght can be considered the probabilty that the statment is true with a given confidence
    """
    question : str = dspy.InputField(desc="The question")
    expected_answer : str = dspy.InputField(desc="The expected answer")
    found_proof : str = dspy.InputField(desc="The found proof")
    proof_matches_expected_answer : float = dspy.OutputField(desc="The similarity between the expected answer and the found proof")

def difficulty_metric(gold: dspy.Example, pred: dspy.Prediction, trace=None, pred_name=None, pred_trace=None):
    metta_handler = MorkHandler()
    compare : dspy.Module = dspy.ChainOfThought(CompareResultSig)
    validate_rule : dspy.Module = dspy.ChainOfThought(ValidateRuleSig)

    log = False

    penalty = 0
    penalty_reason = ""

    if pred.statements == [] or pred.statements is None:
        return dspy.Prediction(score=0.0, feedback="No pln statements found")

    for stmt in pred.statements:
        stmt , score = balance_parentheses(stmt)
        if checkStmt(stmt) == 0.0:
            return dspy.Prediction(score=0.0, feedback=
                f"""The statement {stmt} did not follow the right syntax.
                    it should look like (: proof_name (Predicate x) (STV strength confidence))""")
        metta_handler.add_atom(stmt,log=log)
    
    for qr in pred.queries:
        query = qr['query']
        query , score = balance_parentheses(query)
        if checkQuery(query) == 0.0:
            return dspy.Prediction(score=0.0, feedback=
             f"""The query {query} did not follow the right syntax.
                 It should look like (: $prf (Predicate x) $tv)""")

        for rule in qr['rules']:
            rule , score = balance_parentheses(rule)
            if checkImpl(rule) == 0.0:
                return dspy.Prediction(score=0.0, feedback=
                    f"""One of the pln rules did not follow the right syntax.
                        it should look like (: proof_name (Implication (PredicateA x) (PredicateB x)) (STV strength confidence))""")
            validation = validate_rule(rule=rule)
            if not validation.is_logically_valid:
                return dspy.Prediction(score=0.0, feedback=
                    f"This rule is not logicaly sound: {rule}\nReasoning: {validation.reasoning}")
            metta_handler.add_atom(rule,log=log)

    proofs = []
    for qr in pred.queries:
        clean_query , _ = balance_parentheses(qr['query'])
        proofs.append(metta_handler.query(clean_query,log=log))

    correct_matches = 0
    feedback_details = []
    # Compare each question's proof against its expected answer
    for i, q in enumerate(gold.queries):
        if len(proofs[i]) > 0:
            comparison = compare( question=q['question']
                                , expected_answer=q['expected_answer']
                                , found_proof=proofs[i])
            correct_matches += comparison.proof_matches_expected_answer
            feedback_details.append(dedent(f"""
            Proof:
            {proofs[i]}
            for question:
            '{q['question']}'
            matched expected answer:
            {q['expected_answer']}
            with similarity: {comparison.proof_matches_expected_answer}
            Reasoning: {comparison.reasoning}"""))

            if comparison.proof_matches_expected_answer < 0.7:
                feedback_details.append(dedent(f"""
                A possible representation to solve this problem could be:
                Statments:
                {gold.statements}
                Queries:
                {q['query']}
                Rules:
                {q['rules']}"""))
        else:
            feedback_details.append(dedent(f"""
            No proof found for question '{q['question']}'.
            A possible representation to solve this problem could be:
            Statments:
            {gold.statements}
            Queries:
            {q['query']}
            Rules:
            {q['rules']}
            """))

    total_questions = len(pred.queries)
    score = correct_matches / total_questions if total_questions > 0 else 0.0
    detailed_feedback = f"Score: {correct_matches}/{total_questions} questions matched. \n" + "\n".join(feedback_details)
    return dspy.Prediction(score=score, feedback=detailed_feedback)


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
            dspy.Example(item).with_inputs("sentences", "queries")
        )
    return examples

if __name__ == '__main__':
    #model = "openrouter/google/gemini-2.5-flash-lite"
    #model = "openai/gpt-4o" #{'openai/gpt-4o': {'completion_tokens': 1217, 'prompt_tokens': 5139, 'total_tokens': 6356, 'completion_tokens_details': {'accepted_prediction_tokens': 0, 'audio_tokens': 0, 'reasoning_tokens': 0, 'rejected_prediction_tokens': 0, 'text_tokens': 0}, 'prompt_tokens_details': {'audio_tokens': 0, 'cached_tokens': 1536, 'text_tokens': 0, 'image_tokens': 0}}}
    #model = "openai/o3" #{'openai/o3': {'completion_tokens': 6834, 'prompt_tokens': 5279, 'total_tokens': 12113, 'completion_tokens_details': {'accepted_prediction_tokens': 0, 'audio_tokens': 0, 'reasoning_tokens': 5376, 'rejected_prediction_tokens': 0, 'text_tokens': 0}, 'prompt_tokens_details': {'audio_tokens': 0, 'cached_tokens': 1536, 'text_tokens': 0, 'image_tokens': 0}}}
    #model = "openai/gpt-4.1"
    #model = "openrouter/z-ai/glm-4.6"
    #model = "openrouter/openai/gpt-5"
    #model  = "openrouter/anthropic/claude-haiku-4.5"
    model = "openrouter/openai/gpt-oss-120b"
    #model = "openrouter/qwen/qwen3-235b-a22b-thinking-2507"
    #model = "openrouter/meta-llama/llama-3.3-70b-instruct"

    dspy.configure(lm=dspy.LM(model,temperature=1.0, max_tokens=20000))
    dspy.settings.configure(track_usage=True)

    base_module = SimpleModule(model=model)

    module = dspy.BestOfN(module=base_module, N=20, reward_fn=difficulty_metric, threshold=0.7)
    #module.load("programs/sample_module_optimzied.json")

    puzzle_data = build_examples_from_file("data/sentences.json")

    puzzle_data = [puzzle_data[0]]
    metrics = []
    for puzzle in puzzle_data:
        res = module(gold=puzzle,sentences=puzzle.sentences, queries=puzzle.queries)
        print(res)
        #metric = difficulty_metric(puzzle, res)
        #metrics.append(metric)
    #score_sum = 0
    #for metric in metrics:
    #    score_sum += metric.score
    #    print(metric.score)
    #    print(metric.feedback)
    #print(score_sum/len(metrics))


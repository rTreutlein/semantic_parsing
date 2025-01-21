import dspy
import json
from typing import List, Dict
from dspy.teleprompt import MIPROv2, BootstrapFewShot, COPRO
from dspy.evaluate import Evaluate
from ..nl2pln import NL2PLN
from .cache_handler import CacheHandler

class NL2PLNSignature(dspy.Signature):
    """Convert natural language to predicate logic notation.
    
    Takes a sentence and optional context (similar examples and previous sentences)
    and converts it to predicate logic notation.
    """
    sentence: str = dspy.InputField(desc="Natural language sentence to convert")
    similar: list[str] = dspy.InputField(desc="Similar examples with their conversions")
    previous: list[str] = dspy.InputField(desc="Previous sentences in the conversation")
    statements: list[str] = dspy.OutputField(desc="Generated predicate logic statements")
    type_definitions: list[str] = dspy.OutputField(desc="Generated type definitions")

def my_metric(example: dspy.Example, prediction: dspy.Prediction, trace=None) -> float:
    """
    Compute similarity metric between predicted and expected outputs.
    Returns a score between 0 and 1.
    """
    # Count matches for both statements and type definitions
    statement_matches = len(set(example.statements) & set(prediction.statements))
    type_matches = len(set(example.type_definitions) & set(prediction.type_definitions))
    
    # Get total counts
    total_statements = max(len(example.statements), len(prediction.statements))
    total_types = max(len(example.type_definitions), len(prediction.type_definitions))
    
    # Avoid division by zero
    if total_statements == 0 and total_types == 0:
        return 1.0
    elif total_statements == 0:
        return type_matches / total_types
    elif total_types == 0:
        return statement_matches / total_statements
    
    # Return weighted average
    return 0.7 * (statement_matches / total_statements) + 0.3 * (type_matches / total_types)

def create_training_data(cache_file: str) -> List[dspy.Example]:
    """Create training dataset from verifier cache"""
    cache = CacheHandler(cache_file)
    cache_data = cache._load_cache()
    
    examples = []
    for key, value in cache_data.items():
        try:
            # Parse the cache key (stored as string representation of dict)
            key_dict = eval(key)
            
            # Create example from cache entry
            example = dspy.Example(
                sentence=key_dict["args"][0],
                similar=key_dict["kwargs"].get("similar_examples", []),
                previous=key_dict["kwargs"].get("previous_sentences", []),
                statements=value.get("statements", []),
                type_definitions=value.get("type_definitions", [])
            )
            examples.append(example)
        except:
            continue
            
    # Set inputs for all examples
    return [ex.with_inputs("sentence", "similar", "previous") for ex in examples]

def optimize_MIPRO(program, trainset, mode="light", out="mipro_optimized_nl2pln"):
    """Optimize using MIPROv2"""
    teleprompter = MIPROv2(
        metric=my_metric,
        auto=mode,
        verbose=True
    )
    
    optimized_program = teleprompter.compile(
        program.deepcopy(),
        trainset=trainset,
        requires_permission_to_run=False
    )
    
    optimized_program.save(f"{out}.json")
    return optimized_program

def optimize_BFS(program, dataset, out="bfs_optimized_nl2pln"):
    """Optimize using Bootstrap Few Shot"""
    optimizer = BootstrapFewShot(
        metric=my_metric,
        max_bootstrapped_demos=5,
        max_labeled_demos=5,
        max_rounds=10,
    )

    optimized_program = optimizer.compile(program.deepcopy(), trainset=dataset)
    optimized_program.save(f"{out}.json")
    return optimized_program

def optimize_COPRO(program, trainset, out="copro_optimized_nl2pln"):
    """Optimize using COPRO"""
    teleprompter = COPRO(
        metric=my_metric,
        verbose=True
    )

    kwargs = dict(display_progress=True, display_table=0)
    
    optimized_program = teleprompter.compile(
        program.deepcopy(),
        trainset=trainset,
        eval_kwargs=kwargs
    )

    optimized_program.save(f"{out}.json")
    return optimized_program

def eval(program, dataset):
    """Evaluate program performance on dataset"""
    print("\nRunning optimized program on training set and comparing results:")
    total = 0
    for example in dataset:
        prediction = program(
            sentence=example.sentence,
            similar=example.similar,
            previous=example.previous
        )
        
        metric = my_metric(example, prediction)
        total += metric

        if metric != 1.0:
            print(f"\nExample mismatch (metric {metric}):")
            print(f"Input sentence: {example.sentence}")
            print(f"\nExpected statements:")
            print("\n".join(example.statements))
            print(f"\nActual statements:")
            print("\n".join(prediction.statements))
            print(f"\nExpected type definitions:")
            print("\n".join(example.type_definitions))
            print(f"\nActual type definitions:")
            print("\n".join(prediction.type_definitions))
            print("="*80)
            
    print(f"\nTotal metric: {total/len(dataset)}")

def main():
    # Configure LM
    lm = dspy.LM('anthropic/claude-3-5-sonnet-20241022')
    dspy.configure(lm=lm)

    # Initialize program
    program = NL2PLN(rag=None)  # No RAG needed for optimization

    # Load training data from cache
    trainset = create_training_data("verified_nl2pln.json")

    # Optimize using different methods
    #program = optimize_MIPRO(program, trainset)
    #program = optimize_BFS(program, trainset)
    #program = optimize_COPRO(program, trainset)

    # Evaluate results
    eval(program, trainset)

if __name__ == "__main__":
    main()

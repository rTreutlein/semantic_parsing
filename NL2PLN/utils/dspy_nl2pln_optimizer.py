import dspy
import json
from typing import List, Dict, Optional
from dspy.teleprompt import MIPROv2, BootstrapFewShot, COPRO
from dspy.evaluate import Evaluate
from ..nl2pln import NL2PLN
from .cache_handler import CacheHandler
from .prompts import NL2PLN_Signature

class SemanticSimilarityMetric(dspy.Module):
    """Standalone LLM-based semantic similarity metric"""
    
    def __init__(self):
        super().__init__()
        self.scorer = dspy.Predict('predicted, expected -> similarity_score: float')
    
    def forward(self, example: dspy.Example, prediction: dspy.Prediction, trace=None) -> float:
        """Score semantic similarity between predicted and expected outputs"""
        # Combine statements and typedefs into single strings
        predicted_str = "\n".join(prediction.statements + prediction.typedefs)
        expected_str = "\n".join(example.statements + example.typedefs)
        
        # Get LLM-based similarity score
        result = self.scorer(
            predicted=predicted_str,
            expected=expected_str
        )
        
        try:
            return float(result.similarity_score)
        except (ValueError, AttributeError):
            return 0.0

def my_metric(example: dspy.Example, prediction: dspy.Prediction, trace=None) -> float:
    """
    Compute similarity metric between predicted and expected outputs.
    Returns a score between 0 and 1.
    """
    # Count matches for both statements and type definitions
    statement_matches = len(set(example.statements) & set(prediction.statements))
    type_matches = len(set(example.typedefs) & set(prediction.typedefs))
    
    # Get total counts
    total_statements = max(len(example.statements), len(prediction.statements))
    total_types = max(len(example.typedefs), len(prediction.typedefs))
    
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
                previous=key_dict["kwargs"].get("previous_sentences", []),
                statements=value.get("statements", []),
                typedefs=value.get("typedefs", [])
            )
            examples.append(example)
        except:
            continue
            
    # Set inputs for all examples
    return [ex.with_inputs("sentence", "previous") for ex in examples]

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


def optimize_MIPRO_ZeroShot(program,trainset,mode="light",out="miprozs_optimized"):
    # Initialize MIPROv2 optimizer with light optimization settings
    teleprompter = MIPROv2(
        metric=my_metric,
        auto=mode,  # light/medium/heavy optimization run
        verbose=True
    )
    
    # Optimize the program
    print("Optimizing program with MIPROv2...")
    optimized_program = teleprompter.compile(
        program.deepcopy(),
        trainset=trainset,
        max_bootstrapped_demos=0,
        max_labeled_demos=0,
        requires_permission_to_run=False
    )
    
    # Save the optimized program
    optimized_program.save(f"{out}.json")
    
    return optimized_program

def evaluate(program, dataset, metric_name="semantic"):
    """Evaluate program performance on dataset using specified metric"""
    print(f"\nRunning optimized program on training set using {metric_name} metric:")
    
    # Initialize metrics
    metrics = {
        "exact": my_metric,
        "semantic": SemanticSimilarityMetric()
    }
    
    # Get selected metric
    metric = metrics.get(metric_name, metrics["semantic"])
    
    total = 0
    for example in dataset:
        prediction = program(
            sentence=example.sentence,
            previous=example.previous,
            similar=[]
        )
        
        score = metric(example, prediction)
        total += score
        if score != 1.0:
            print(f"\nExample mismatch (score {score}):")
            print(f"Input sentence: {example.sentence}")
            print(f"\nExpected statements:")
            print("\n".join(example.statements))
            print(f"\nActual statements:")
            print("\n".join(prediction.statements))
            print(f"\nExpected type definitions:")
            print("\n".join(example.typedefs))
            print(f"\nActual type definitions:")
            print("\n".join(prediction.typedefs))
            print("="*80)
            dspy.inspect_history(n=1)
            exit()
            
    print(f"\nAverage {metric_name} score: {total/len(dataset)}")

def main():
    # Configure LM
    lm = dspy.LM('anthropic/claude-3-5-sonnet-20241022')
    dspy.configure(lm=lm)

    # Initialize program
    program = dspy.ChainOfThought(NL2PLN_Signature) # No RAG needed for optimization

    # Load training data from cache
    trainset = create_training_data("johnnoperformative_verified_nl2pln.json")

    # Optimize using different methods
    #program = optimize_MIPRO(program, trainset)
    #program = optimize_BFS(program, trainset)
    #program = optimize_COPRO(program, trainset)

    # Evaluate results
    evaluate(program, trainset)

if __name__ == "__main__":
    main()

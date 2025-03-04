import dspy
import json
import os
from tabulate import tabulate

# Load the same LM as in promptgen.py
lm = dspy.LM('openrouter/anthropic/claude-3.7-sonnet')
dspy.configure(lm=lm)

def load_samples():
    """Load the generated samples from the JSON file."""
    try:
        with open("samples/generated_samples.json", "r") as f:
            samples = json.load(f)
        return samples
    except FileNotFoundError:
        print("Error: samples/generated_samples.json not found.")
        return []

def load_optimized_task():
    """Load the optimized task from the saved file."""
    try:
        # Load the optimized task
        optimized_task = dspy.Module.load("task.json")
        return optimized_task
    except FileNotFoundError:
        print("Error: task.json not found. Run promptgen.py first.")
        return None

def evaluate_model(model, samples):
    """Evaluate the model on the samples and return metrics."""
    if not model or not samples:
        return []
    
    results = []
    
    for i, sample in enumerate(samples):
        english = sample["input"]
        expected_types = sample["types"]
        expected_statements = sample["statements"]
        expected_questions = sample.get("questions", "")
        
        # Run the model on the input
        prediction = model(english=english)
        
        # Calculate simple similarity metrics (could be improved)
        types_match = expected_types.strip() == prediction.pln_types.strip()
        statements_match = expected_statements.strip() == prediction.pln_statements.strip()
        questions_match = expected_questions.strip() == prediction.pln_questions.strip()
        
        # Store the results
        results.append({
            "sample_id": i,
            "input": english,
            "types_match": types_match,
            "statements_match": statements_match,
            "questions_match": questions_match,
            "expected_types": expected_types,
            "predicted_types": prediction.pln_types,
            "expected_statements": expected_statements,
            "predicted_statements": prediction.pln_statements,
            "expected_questions": expected_questions,
            "predicted_questions": prediction.pln_questions
        })
    
    return results

def print_evaluation_summary(results):
    """Print a summary of the evaluation results."""
    if not results:
        print("No results to display.")
        return
    
    # Calculate overall metrics
    total = len(results)
    types_correct = sum(1 for r in results if r["types_match"])
    statements_correct = sum(1 for r in results if r["statements_match"])
    questions_correct = sum(1 for r in results if r["questions_match"])
    all_correct = sum(1 for r in results if r["types_match"] and r["statements_match"] and r["questions_match"])
    
    # Print summary table
    summary_data = [
        ["Types Correct", f"{types_correct}/{total}", f"{types_correct/total:.2%}"],
        ["Statements Correct", f"{statements_correct}/{total}", f"{statements_correct/total:.2%}"],
        ["Questions Correct", f"{questions_correct}/{total}", f"{questions_correct/total:.2%}"],
        ["All Components Correct", f"{all_correct}/{total}", f"{all_correct/total:.2%}"]
    ]
    
    print("\n=== Evaluation Summary ===")
    print(tabulate(summary_data, headers=["Metric", "Count", "Percentage"], tablefmt="grid"))
    
    # Print detailed results for each sample
    print("\n=== Detailed Results ===")
    for i, result in enumerate(results):
        print(f"\nSample {i+1}: {result['input']}")
        print(f"  Types Match: {'✓' if result['types_match'] else '✗'}")
        print(f"  Statements Match: {'✓' if result['statements_match'] else '✗'}")
        print(f"  Questions Match: {'✓' if result['questions_match'] else '✗'}")
        
        if not result['types_match']:
            print("\n  Expected Types:")
            print(f"    {result['expected_types']}")
            print("  Predicted Types:")
            print(f"    {result['predicted_types']}")
        
        if not result['statements_match']:
            print("\n  Expected Statements:")
            print(f"    {result['expected_statements']}")
            print("  Predicted Statements:")
            print(f"    {result['predicted_statements']}")
        
        if not result['questions_match'] and result['expected_questions']:
            print("\n  Expected Questions:")
            print(f"    {result['expected_questions']}")
            print("  Predicted Questions:")
            print(f"    {result['predicted_questions']}")

def main():
    print("Loading samples...")
    samples = load_samples()
    if not samples:
        return
    
    print(f"Loaded {len(samples)} samples.")
    
    print("Loading optimized task...")
    optimized_task = load_optimized_task()
    if not optimized_task:
        return
    
    print("Evaluating model on samples...")
    results = evaluate_model(optimized_task, samples)
    
    print_evaluation_summary(results)

if __name__ == "__main__":
    main()

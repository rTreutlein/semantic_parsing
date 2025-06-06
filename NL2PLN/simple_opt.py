import dspy
import json
from pathlib import Path
from typing import List
from dspy.teleprompt import MIPROv2
from NL2PLN.simple_puzzle_manager import SimplePuzzleProcessor
from NL2PLN.simple_nl2pln import SimpleNL2PLN

def load_medium_puzzles_dataset(medium_puzzles_dir: str) -> List[dspy.Prediction]:
    """
    Load all puzzles saved with --store-medium as a dataset.
    
    Args:
        medium_puzzles_dir: Directory containing the saved medium difficulty puzzles
        
    Returns:
        List of dspy.Prediction objects loaded from the JSON files
    """
    dataset = []
    puzzles_path = Path(medium_puzzles_dir)
    
    if not puzzles_path.exists():
        print(f"Warning: Directory {medium_puzzles_dir} does not exist")
        return dataset
    
    # Find all JSON files in the directory
    json_files = list(puzzles_path.glob("puzzle*.json"))
    
    if not json_files:
        print(f"Warning: No puzzle JSON files found in {medium_puzzles_dir}")
        return dataset
    
    print(f"Loading {len(json_files)} puzzles from {medium_puzzles_dir}")
    
    for json_file in json_files:
        try:
            with open(json_file, 'r') as f:
                puzzle_data = json.load(f)
            
            # Convert back to dspy.Example
            puzzle = dspy.Example(**puzzle_data).with_inputs("sentences")
            dataset.append(puzzle)
            
        except Exception as e:
            print(f"Error loading puzzle from {json_file}: {e}")
            continue
    
    print(f"Successfully loaded {len(dataset)} puzzles")
    return dataset

# Initialize the LM
lm = dspy.LM('openrouter/anthropic/claude-sonnet-4')
dspy.configure(lm=lm)

processor = SimplePuzzleProcessor("optimization")

# Initialize optimizer
teleprompter = MIPROv2(
    metric=processor.process_puzzle,
    auto="medium", # Can choose between light, medium, and heavy optimization runs
)

# Load training dataset from medium difficulty puzzles
# Replace 'path/to/medium/puzzles' with the actual directory path
trainset = load_medium_puzzles_dataset('puzzle')

# Optimize program
print(f"Optimizing program with MIPROv2...")
optimized_program = teleprompter.compile(
    SimpleNL2PLN(n=3),
    trainset=trainset,
    requires_permission_to_run=False,
)

# Save optimize program for future use
optimized_program.save(f"optimized.json")

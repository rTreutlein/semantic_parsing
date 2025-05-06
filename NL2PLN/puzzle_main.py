import argparse
import dspy
import json
from pathlib import Path
from NL2PLN.utils.puzzle_generator import LogicPuzzleGenerator
from NL2PLN.tests.example_puzzle import ExamplePuzzleGenerator
from NL2PLN.puzzle_manager import PuzzleProcessor

def configure_lm(model_name: str = 'anthropic/claude-3-5-sonnet-20241022'):
    """Configure the LM for DSPY."""
    lm = dspy.LM(model_name)
    dspy.configure(lm=lm)

def main():
    parser = argparse.ArgumentParser(description="Generate and process logic puzzles using OpenCog PLN.")
    parser.add_argument("--output", default="puzzle", help="Base name for output files")
    parser.add_argument("--num-puzzles", type=int, default=1, help="Number of puzzles to generate")
    parser.add_argument("--example", action="store_true", help="Run the example puzzle")
    parser.add_argument("--verify", action="store_true", help="Verify the NL2PLN module")
    parser.add_argument("--save-puzzle", help="Save generated puzzle to JSON file")
    parser.add_argument("--load-puzzle", help="Load puzzle from JSON file instead of generating")
    args = parser.parse_args()

    # Configure LM
    #configure_lm('deepseek/deepseek-reasoner')
    configure_lm()

    # Initialize puzzle generator and processor
    puzzle_gen = ExamplePuzzleGenerator() if args.example else LogicPuzzleGenerator()
    processor = PuzzleProcessor(args.output, reset_db=args.example, verify=args.verify)
    
    for i in range(args.num_puzzles):
        print(f"\nProcessing puzzle {i+1}/{args.num_puzzles}")
        
        if args.load_puzzle:
            # Load puzzle from file
            with open(args.load_puzzle) as f:
                puzzle_data = json.load(f)
            puzzle = dspy.Prediction(**puzzle_data)
        else:
            # Generate new puzzle
            puzzle = puzzle_gen.generate_puzzle(numberOfPremises=5)
            
            if args.save_puzzle:
                # Save puzzle to file
                print(puzzle)
                print(puzzle.__dict__['_store'])
                Path(args.save_puzzle).parent.mkdir(parents=True, exist_ok=True)
                with open(args.save_puzzle, 'w') as f:
                    json.dump(puzzle.__dict__['_store'], f, indent=2)
        
        processor.process_puzzle(puzzle)

if __name__ == "__main__":
    main()

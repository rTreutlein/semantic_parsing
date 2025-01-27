import argparse
import dspy
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
    args = parser.parse_args()

    # Configure LM
    configure_lm('deepseek/deepseek-reasoner')

    # Initialize puzzle generator and processor
    puzzle_gen = ExamplePuzzleGenerator() if args.example else LogicPuzzleGenerator()
    processor = PuzzleProcessor(args.output, reset_db=args.example, verify=args.verify)
    
    for i in range(args.num_puzzles):
        print(f"\nGenerating puzzle {i+1}/{args.num_puzzles}")
        puzzle = puzzle_gen.generate_puzzle(numberOfPremises=2)
        processor.process_puzzle(puzzle)

if __name__ == "__main__":
    main()

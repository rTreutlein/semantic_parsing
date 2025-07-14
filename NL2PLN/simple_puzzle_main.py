import argparse
import dspy
import json
import datetime
from pathlib import Path
from NL2PLN.simple_puzzle_manager import SimplePuzzleProcessor
from NL2PLN.utils.sample_generator import SampleGenerator
from NL2PLN.simple_nl2pln import SimpleNL2PLN

import logging

logging.basicConfig(
    format="%(asctime)s [%(levelname)s] %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

PUZZLES_PER_LEVEL = 3

def configure_lm(model_name: str = 'openai/gpt-4o'):
    """Configure the LM for DSPY."""
    lm = dspy.LM(model_name)
    dspy.configure(lm=lm)

def generate_samples(num_puzzles: int, output_dir: str, verify: bool = False):
    """Generate samples with increasing difficulty, collecting 3 medium-difficulty puzzles per sentence count."""
    puzzle_gen = SampleGenerator()
    nl2pln = SimpleNL2PLN(n=5)
    nl2pln.load(f"optimized.json")
    processor = SimplePuzzleProcessor("sample",nl2pln=nl2pln,verify=verify)
    
    storage_dir = Path(output_dir)
    storage_dir.mkdir(parents=True, exist_ok=True)
    
    total_saved = 0
    num_sentences = 6
    
    while total_saved < num_puzzles:
        logger.info(f"Generating puzzles with {num_sentences} sentences...")
        saved_for_this_level = 0
        attempts = 0
        max_attempts = 100  # Prevent infinite loops
        
        while saved_for_this_level < PUZZLES_PER_LEVEL and total_saved < num_puzzles and attempts < max_attempts:
            attempts += 1
            logger.info(f"Attempt {attempts} for {num_sentences} sentences (saved: {saved_for_this_level}/{PUZZLES_PER_LEVEL})")
            
            # Generate puzzle
            puzzle = puzzle_gen.generate_sample(numberOfSentences=num_sentences)
            score = processor.process_puzzle(puzzle)
            
            # Check if it's medium difficulty (score != 0 and != 1)
            if score != 0 and score != 1:
                puzzle_filename = f"puzzle_sentences_{num_sentences}_count_{saved_for_this_level + 1}_score_{score}_{datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.json"
                puzzle_path = storage_dir / puzzle_filename
                
                with open(puzzle_path, 'w') as f:
                    json.dump(puzzle.__dict__['_store'], f, indent=2)
                
                saved_for_this_level += 1
                total_saved += 1
                logger.info(f"Saved medium difficulty puzzle (score: {score}) to {puzzle_path}")
                logger.info(f"Progress: {total_saved}/{num_puzzles} total puzzles saved")
        
        if attempts >= max_attempts:
            logger.warning(f"Reached maximum attempts ({max_attempts}) for {num_sentences} sentences")
        
        num_sentences += 1
        
        # Safety check to prevent infinite loop
        if num_sentences > 10:
            logger.warning("Reached maximum sentence count (10), stopping generation")
            break
    
    logger.info(f"Generation complete! Saved {total_saved} puzzles to {storage_dir} using {attempts} attempts.")

def main():
    parser = argparse.ArgumentParser(description="Generate and process logic puzzles using OpenCog PLN.")
    parser.add_argument("--output", default="puzzle", help="Base name for output files")
    parser.add_argument("--num-puzzles", type=int, default=1, help="Number of puzzles to generate")
    parser.add_argument("--verify", action="store_true", help="Verify the NL2PLN module")
    parser.add_argument("--save-puzzle", help="Save generated puzzle to JSON file")
    parser.add_argument("--load-puzzle", help="Load puzzle from JSON file instead of generating")
    parser.add_argument("--generate-samples", help="Directory to generate and store sample puzzles with medium difficulty")
    args = parser.parse_args()

    # Configure LM
    #configure_lm('deepseek/deepseek-reasoner')
    configure_lm('openrouter/anthropic/claude-sonnet-4')

    # Check if we should generate samples
    if args.generate_samples:
        generate_samples(args.num_puzzles, args.generate_samples, args.verify)
        return

    # Initialize puzzle generator and processor
    puzzle_gen = SampleGenerator()
    processor = SimplePuzzleProcessor(args.output, verify=args.verify)
    
    for i in range(args.num_puzzles):
        logger.info(f"Processing puzzle {i+1}/{args.num_puzzles}")
        
        if args.load_puzzle:
            # Load puzzle from file
            with open(args.load_puzzle) as f:
                puzzle_data = json.load(f)
            puzzle = dspy.Prediction(**puzzle_data)
        else:
            # Generate new puzzle
            puzzle = puzzle_gen.generate_sample(numberOfSentences=3)
            
            if args.save_puzzle:
                # Save puzzle to file
                print(puzzle)
                print(puzzle.__dict__['_store'])
                Path(args.save_puzzle).parent.mkdir(parents=True, exist_ok=True)
                with open(args.save_puzzle, 'w') as f:
                    json.dump(puzzle.__dict__['_store'], f, indent=2)
        
        logger.info("Processed puzzle:")
        print(puzzle)
        score = processor.process_puzzle(puzzle)

if __name__ == "__main__":
    main()

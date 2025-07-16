import argparse
import dspy
import json
import datetime
from pathlib import Path
from NL2PLN.simple_puzzle_manager import SimplePuzzleProcessor
from NL2PLN.utils.sample_generator import SampleGenerator
from NL2PLN.simple_nl2pln import SimpleNL2PLN

import logging
import concurrent.futures
import queue

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

def generate_samples(num_puzzles: int, output_dir: str, verify: bool = False, max_workers: int = 4):
    """
    Generate samples with increasing difficulty, collecting 3 medium-difficulty
    puzzles per sentence count.

    Puzzle generation and processing are executed concurrently: a background
    worker creates puzzles and immediately feeds them to a queue that a thread
    pool pulls from to perform the expensive `process_puzzle` calls.
    """
    puzzle_gen = SampleGenerator()
    nl2pln = SimpleNL2PLN(n=5)
    nl2pln.load("optimized.json")
    processor = SimplePuzzleProcessor("sample", nl2pln=nl2pln, verify=verify)

    storage_dir = Path(output_dir)
    storage_dir.mkdir(parents=True, exist_ok=True)

    total_saved = 0
    num_sentences = 6
    max_attempts = 100  # per difficulty level

    # Result queue shared between workers and the main thread
    result_queue: queue.Queue[tuple] = queue.Queue(maxsize=max_workers * 2)

    def worker(sentence_count: int):
        """Generate a puzzle and process it, then put the result on the queue."""
        try:
            puzzle = puzzle_gen.generate_sample(numberOfSentences=sentence_count)
            score = processor.process_puzzle(puzzle)
            result_queue.put((puzzle, score, sentence_count), block=True)
        except Exception as exc:
            logger.exception("Worker failed: %s", exc)

    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        while total_saved < num_puzzles and num_sentences <= 10:
            logger.info("Generating puzzles with %s sentences…", num_sentences)
            saved_for_this_level = 0
            attempts = 0

            # Kick off an initial batch of at most `max_workers` workers
            initial_batch = min(max_workers, max_attempts)
            active_workers = 0
            for _ in range(initial_batch):
                executor.submit(worker, num_sentences)
                attempts += 1
                active_workers += 1

            # Consume and launch workers until we collect enough medium puzzles
            while saved_for_this_level < PUZZLES_PER_LEVEL and total_saved < num_puzzles and attempts < max_attempts:
                # Refill the pool so that at most `max_workers` tasks are running
                while active_workers < max_workers and attempts < max_attempts:
                    executor.submit(worker, num_sentences)
                    attempts += 1
                    active_workers += 1

                try:
                    puzzle, score, sentence_count = result_queue.get(timeout=120)
                    active_workers -= 1  # one worker finished
                    logger.info(f"Received puzzle: {puzzle} with score: {score}")
                except queue.Empty:
                    logger.warning("No puzzle returned within 120 s – continuing")
                    continue

                try:
                    puzzle, score, sentence_count = result_queue.get(timeout=120)
                    logger.info(f"Received puzzle: {puzzle} with score: {score}")
                except queue.Empty:
                    logger.warning("No puzzle returned within 120 s – continuing")
                    continue

                # Medium difficulty check
                if score not in (0, 1):
                    filename = (
                        f"puzzle_sentences_{sentence_count}_count_{saved_for_this_level + 1}"
                        f"_score_{score}_{datetime.datetime.now():%Y-%m-%d_%H-%M-%S'}.json"
                    )
                    path = storage_dir / filename
                    with open(path, "w") as f:
                        json.dump(puzzle.__dict__['_store'], f, indent=2)

                    saved_for_this_level += 1
                    total_saved += 1
                    logger.info(
                        "Saved medium difficulty puzzle (score: %s) to %s", score, path
                    )
                    logger.info(
                        "Progress: %s/%s total puzzles saved", total_saved, num_puzzles
                    )

            if attempts >= max_attempts:
                logger.warning(
                    "Reached maximum attempts (%s) for %s sentences",
                    max_attempts,
                    num_sentences,
                )

            num_sentences += 1

    logger.info("Generation complete! Saved %s puzzles to %s", total_saved, storage_dir)

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
    nl2pln = SimpleNL2PLN(n=5)
    nl2pln.load("optimized.json")
    processor = SimplePuzzleProcessor(args.output, nl2pln=nl2pln, verify=args.verify)
    
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

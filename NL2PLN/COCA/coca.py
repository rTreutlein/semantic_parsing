from __future__ import annotations

import argparse
import random
import sys
from pathlib import Path
from typing import Iterator, List, Optional


def is_valid_line(line: str, max_words: int) -> bool:
    """
    Returns True if the line is non-empty and has at most `max_words` words.
    """
    stripped = line.strip()
    if not stripped:
        return False
    # Count words by whitespace separation
    return len(stripped.split()) <= max_words


def iter_candidate_lines(directory: Path, max_words: int) -> Iterator[str]:
    """
    Yields candidate lines from all .txt files in the given directory
    that have at most `max_words` words.
    """
    for txt_file in sorted(directory.glob("*.txt")):
        try:
            with txt_file.open("r", encoding="utf-8", errors="ignore") as f:
                for raw_line in f:
                    line = raw_line.strip()
                    if is_valid_line(line, max_words):
                        yield line
        except Exception as e:
            print(f"Warning: failed to read {txt_file}: {e}", file=sys.stderr)


def reservoir_sample(iterable: Iterator[str], k: int, rng: random.Random) -> List[str]:
    """
    Uniformly sample k items from an iterator of unknown/large size using reservoir sampling.

    Note:
        This does not "take the first k items." It fills the reservoir with the first k
        items, then for each subsequent item i, replaces a random element with probability k/(i+1),
        which yields an unbiased uniform sample without reading all items into memory.
    """
    reservoir: List[str] = []
    for i, item in enumerate(iterable):
        if i < k:
            reservoir.append(item)
        else:
            j = rng.randint(0, i)
            if j < k:
                reservoir[j] = item
    return reservoir


def sample_random_lines_from_folder(
    folder: Path, count: int = 10, max_words: int = 100, seed: Optional[int] = None
) -> List[str]:
    """
    Samples up to `count` random lines from .txt files in `folder`,
    where each line has at most `max_words` words.
    """
    rng = random.Random(seed)
    candidates = iter_candidate_lines(folder, max_words)
    samples = reservoir_sample(candidates, count, rng)
    if len(samples) < count:
        print(
            f"Note: only found {len(samples)} eligible lines (requested {count}).",
            file=sys.stderr,
        )
    return samples


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Sample random lines from .txt files in this folder (max word length constraint)."
    )
    parser.add_argument(
        "--count", type=int, default=10, help="Number of lines to sample (default: 10)"
    )
    parser.add_argument(
        "--max-words", type=int, default=100, help="Maximum words per line (default: 100)"
    )
    parser.add_argument(
        "--seed", type=int, default=None, help="Optional RNG seed for reproducibility"
    )
    parser.add_argument(
        "--output", type=Path, default=None, help="Optional output file to write samples"
    )
    args = parser.parse_args()

    folder = Path(__file__).parent
    lines = sample_random_lines_from_folder(
        folder=folder, count=args.count, max_words=args.max_words, seed=args.seed
    )
    if args.output:
        try:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            with args.output.open("w", encoding="utf-8") as out:
                for line in lines:
                    out.write(line + "\n")
        except Exception as e:
            print(f"Error: failed to write to {args.output}: {e}", file=sys.stderr)
            sys.exit(1)
    else:
        for line in lines:
            print(line)


if __name__ == "__main__":
    main()

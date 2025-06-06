import dspy
from dspy.teleprompt import MIPROv2
from simple_puzzle_manager import SimplePuzzleProcessor
from NL2PLN.simple_nl2pln import SimpleNL2PLN

# Initialize the LM
lm = dspy.LM('openrouter/anthropic/claude-sonnet-4')
dspy.configure(lm=lm)

processor = SimplePuzzleProcessor("optimization")

# Initialize optimizer
teleprompter = MIPROv2(
    metric=processor.process_puzzle,
    auto="medium", # Can choose between light, medium, and heavy optimization runs
)

# Optimize program
print(f"Optimizing program with MIPROv2...")
optimized_program = teleprompter.compile(
    SimpleNL2PLN(n=3),
    trainset=gsm8k.train,
    requires_permission_to_run=False,
)

# Save optimize program for future use
optimized_program.save(f"optimized.json")

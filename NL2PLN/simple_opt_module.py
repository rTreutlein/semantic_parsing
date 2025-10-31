from typing import List
import argparse
import json
import random
import litellm
import mlflow

litellm.drop_params = True

import dspy
from dspy.teleprompt import GEPA

from NL2PLN.simple_module import SimpleModule , difficulty_metric

# --------------------------------------------------------------------------- #
#  LM configuration                                                           #
# --------------------------------------------------------------------------- #
#dspy.configure(lm=dspy.LM("openrouter/anthropic/claude-sonnet-4"))
#model = "openai/gpt-5"
#model = "openrouter/z-ai/glm-4.5"
#model = "openrouter/openai/gpt-oss-120b"
model = "openrouter/qwen/qwen3-235b-a22b-thinking-2507"
#model = "openrouter/openai/gpt-5"
optmodel = model

dspy.configure(lm=dspy.LM(model,temperature=1.0, max_tokens=20000))

mlflow.dspy.autolog(
    log_compiles=True,    # Track optimization process
    log_evals=True,       # Track evaluation results
    log_traces_from_compile=True  # Track program traces during optimization
)

mlflow.set_tracking_uri(uri="http://127.0.0.1:5000")
mlflow.set_experiment("DSPy-Optimization")

# --------------------------------------------------------------------------- #
#  Optimisation                                                               #
# --------------------------------------------------------------------------- #
#parser = argparse.ArgumentParser(
#    description="Optimize SampleGenerator using COCA train/val datasets"
#)
#parser.add_argument("--train-file", type=str, default="NL2PLN/COCA/train.txt",
#                    help="Path to training text file (one sentence per line)")
#parser.add_argument("--val-file", type=str, default="NL2PLN/COCA/val.txt",
#                    help="Path to validation text file (one sentence per line)")
#args = parser.parse_args()

trainset = build_examples_from_file("data/sentences.json")
#valset = build_examples_from_file(args.val_file)

trainset = [trainset[5]]

teleprompter = GEPA(metric=difficulty_metric
                   ,reflection_lm=dspy.LM(model=optmodel, temperature=1.0, max_tokens=32000)
                   ,num_threads=10
                   ,max_full_evals=30
                   ,track_stats=True
                   ,log_dir="gepa_log"
                   )

module = SimpleModule(model=model)
module.load("programs/sample_module_optimzied_17102025_1421.json")

generator_optimised = teleprompter.compile(
    module,
    trainset=trainset,
    #valset=valset,
)

print(generator_optimised.detailed_results)

generator_optimised.save("programs/sample_module_optimzied.json")
print("Optimised generator saved to sample_module_optimzied.json")

import dspy
import json
import os
from utils.checker import human_verify_prediction


lm = dspy.LM('anthropic/claude-3-7-sonnet-20250219')
dspy.configure(lm=lm)

task = "Convert English to Logic (MeTTa PLN Light)"

gen_example = dspy.ChainOfThought('task: str, previous_examples -> diverse_example_input: str, diverse_example_output: str')

# Create samples directory if it doesn't exist
os.makedirs("samples", exist_ok=True)

samples = []
samples_data = []
try:
    with open("samples/generated_samples.json", "r") as f:
        samples = json.load(f)
    samples_data = [dspy.Prediction(input=d["input"], output=d["output"]) for d in samples]
except FileNotFoundError:
    # File doesn't exist yet, that's okay
    pass

if len(samples_data) == 0:
    samples_data = [dspy.Prediction(input="Max is a Dog",
                            output="""Types:
(: dog (-> (: $dog Object) Type))
(: name (-> (: $named Object) (: $name String) Type))

Statements:
(: max Object)
(: max_named_max (WithTV (name max 'Max') (STV 1.0 1.0)))
(: max_dog (WithTV (dog max) (STV 1.0 1.0)))
""")]

for i in range(3):
    pred = gen_example(task=task, previous_examples=samples_data)
    checked_pred = human_verify_prediction(pred, "")
    samples_data.append(checked_pred)

# Save generated samples to a file
samples = [{"input": d.diverse_example_input, "output": d.diverse_example_output} for d in samples_data]
with open("samples/generated_samples.json", "w") as f:
    json.dump(samples_data, f, indent=2)

data = [dspy.Example(input=d.diverse_example_input, output=d.diverse_example_output).with_inputs('input') for d in samples_data]

task = dspy.ChainOfThought('input -> output: str')

def metric(example, pred, trace=None):
    judge = dspy.ChainOfThought('true_output, predicted_output -> similarity: float')
    return judge(true_output=example.output, predicted_output=pred.output)

optimized_task = dspy.MIPROv2(metric=metric, auto="light").compile(task, trainset=data)

optimized_task.save("task.json",save_program=False)

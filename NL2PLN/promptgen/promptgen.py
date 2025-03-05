import dspy
import json
import os
from utils.checker import human_verify_prediction


#lm = dspy.LM('anthropic/claude-3-7-sonnet-20250219')
lm = dspy.LM('openrouter/anthropic/claude-3.7-sonnet')
dspy.configure(lm=lm)

try:
    with open("task.json", "r") as f:
        task = json.load(f)["self"]["extended_signature"]["instructions"]
except Exception as e:
    print(e)
    task = "Convert English to Logic (MeTTa PLN Light)"

gen_example = dspy.ChainOfThought('task: str, previous_examples -> diverse_example_input: str, diverse_example_output_types: str, diverse_example_output_statements: str, diverse_example_output_questions: str')

# Create samples directory if it doesn't exist
os.makedirs("samples", exist_ok=True)

samples = []
samples_data = []
try:
    with open("samples/generated_samples.json", "r") as f:
        samples = json.load(f)
    samples_data = [dspy.Prediction(
        diverse_example_input=d["input"], 
        diverse_example_output_types=d["types"],
        diverse_example_output_statements=d["statements"],
        diverse_example_output_questions=d.get("questions", "")
    ) for d in samples]
except FileNotFoundError:
    # File doesn't exist yet, that's okay
    pass

if len(samples_data) == 0:
    samples_data = [dspy.Prediction(
        diverse_example_input="Max is a Dog",
        diverse_example_output_types="""(: dog (-> (: $dog Object) Type))
(: name (-> (: $named Object) (: $name String) Type))""",
        diverse_example_output_statements="""(: max Object)
(: max_named_max (WithTV (name max 'Max') (STV 1.0 1.0)))
(: max_dog (WithTV (dog max) (STV 1.0 1.0)))""",
        diverse_example_output_questions=""
    )]

for i in range(3):
    pred = gen_example(task=task, previous_examples=samples_data)
    checked_pred = human_verify_prediction(pred, "")
    samples_data.append(checked_pred)

# Save generated samples to a file
samples = [
    {
        "input": d.diverse_example_input, 
        "types": d.diverse_example_output_types,
        "statements": d.diverse_example_output_statements,
        "questions": d.diverse_example_output_questions
    } 
    for d in samples_data
]
with open("samples/generated_samples.json", "w") as f:
    json.dump(samples, f, indent=2)

data = [
    dspy.Example(
        english=d.diverse_example_input, 
        pln_types=d.diverse_example_output_types,
        pln_statements=d.diverse_example_output_statements,
        pln_questions=d.diverse_example_output_questions
    ).with_inputs('english') 
    for d in samples_data
]

task = dspy.ChainOfThought('english -> pln_types: str, pln_statements: str, pln_questions: str')

def metric(example, pred, trace=None):
    judge = dspy.ChainOfThought('true_types, true_statements, true_questions, pred_types, pred_statements, pred_questions -> similarity: float')
    return judge(
        true_types=example.pln_types, 
        true_statements=example.pln_statements,
        true_questions=example.pln_questions,
        pred_types=pred.pln_types,
        pred_statements=pred.pln_statements,
        pred_questions=pred.pln_questions
    ).similarity

optimized_task = dspy.MIPROv2(metric=metric, auto="light").compile(task, trainset=data)

optimized_task.save("./program/",save_program=True)


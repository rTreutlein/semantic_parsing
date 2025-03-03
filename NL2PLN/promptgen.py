import dspy
from utils.checker import human_verify_prediction


lm = dspy.LM('anthropic/claude-3-7-sonnet-20250219')
dspy.configure(lm=lm)

task = "Convert English to Logic (MeTTa PLN Light)"

gen_example = dspy.ChainOfThought('task: str, previous_examples -> diverse_example_input: str, diverse_example_output: str')

data_gen = [dspy.Prediction(input="Max is a Dog",
                            output="""Types:
(: dog (-> (: $dog Object) Type))
(: name (-> (: $named Object) (: $name String) Type))

Statements:
(: max Object)
(: max_named_max (WithTV (name max 'Max') (STV 1.0 1.0)))
(: max_dog (WithTV (dog max) (STV 1.0 1.0)))
""")]

for i in range(3):
    pred = gen_example(task=task, previous_examples=data_gen)
    checked_pred = human_verify_prediction(pred, "")
    data_gen.append(checked_pred)

data = [dspy.Example(input=d.diverse_example_input, output=d.diverse_example_output).with_inputs('input') for d in data_gen]

task = dspy.ChainOfThought('input -> output: str')

def metric(example, pred, trace=None):
    judge = dspy.ChainOfThought('true_output, predicted_output -> similarity: float')
    return judge(true_output=example.output, predicted_output=pred.output)

optimized_task = dspy.MIPROv2(metric=metric, auto="light").compile(task, trainset=data)

optimized_task.save("task.json",save_program=False)

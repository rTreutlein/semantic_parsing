import dspy
from typing import List, Dict
from dspy.teleprompt import BootstrapFewShot
from dspy.evaluate import Evaluate

class TypeAnalyzer(dspy.Module):
    def __init__(self):
        super().__init__()
        self.analyze = dspy.Predict("Given the following types, generate logical linking statements between them. "
                                  "Only use valid MeTTa statements and operators like ->, Not.\n\n"
                                  "Examples:\n"
                                  "1. Simple inheritance:\n"
                                  "Type 1: (: Apple (-> (: $apple Object) Type))\n"
                                  "Type 2: (: Fruit (-> (: $fruit Object) Type))\n"
                                  "Relationship: (: AppleIsFruit (-> (: $a (Apple $a)) (Fruit $a)))\n\n"
                                  "2. Action negation:\n"
                                  "Type 1: (: ToLeave (-> (: $person Object) (: $location Object) Type))\n"
                                  "Type 2: (: ToStay (-> (: $person Object) (: $location Object) Type))\n"
                                  "Relationship: (: ToLeaveToNotToStay (-> (: $l (ToLeave $a $b)) (Not (ToLeave $a $b))))\n\n"
                                  "New types: {new_types}\n"
                                  "Similar existing types: {similar_types}")
    
    def forward(self, new_types: List[str], similar_types: List[str]):
        prediction = self.analyze(new_types="\n".join(new_types), 
                                similar_types="\n".join(similar_types))
        return prediction.statements.split("\n")

class ValidMeTTaMetric(dspy.Metric):
    def __init__(self):
        super().__init__()
        
    def __call__(self, example, pred, trace=None):
        # Basic validation - check if all statements start with (: and end with )
        valid_count = 0
        for statement in pred:
            if statement.strip().startswith("(:") and statement.strip().endswith(")"):
                valid_count += 1
        return valid_count / len(pred) if pred else 0

def create_training_data():
    return [
        dspy.Example(
            new_types=["(: Apple (-> (: $apple Object) Type))"],
            similar_types=["(: Fruit (-> (: $fruit Object) Type))"],
            statements=["(: AppleIsFruit (-> (: $a (Apple $a)) (Fruit $a)))"]
        ),
        dspy.Example(
            new_types=["(: ToLeave (-> (: $person Object) (: $location Object) Type))"],
            similar_types=["(: ToStay (-> (: $person Object) (: $location Object) Type))"],
            statements=[
                "(: ToLeaveToNotToStay (-> (: $l (ToLeave $a $b)) (Not (ToLeave $a $b))))",
                "(: ToStayToNotToLeave (-> (: $t (ToStay $a $b)) (Not (ToStay $a $b))))"
            ]
        ),
        # Add more examples...
    ]

def optimize_prompt():
    # Initialize DSPy settings
    lm = dspy.OpenAI(model='gpt-4')
    dspy.settings.configure(lm=lm)
    
    # Create training data
    trainset = create_training_data()
    
    # Create the base program
    program = TypeAnalyzer()
    
    # Set up evaluation
    evaluate = Evaluate(devset=trainset, metric=ValidMeTTaMetric(), num_threads=4)
    
    # Optimize the prompt
    teleprompter = BootstrapFewShot(metric=ValidMeTTaMetric())
    optimized_program = teleprompter.compile(program, trainset=trainset)
    
    # Evaluate the optimized program
    score = evaluate(optimized_program)
    print(f"Optimized program score: {score}")
    
    return optimized_program

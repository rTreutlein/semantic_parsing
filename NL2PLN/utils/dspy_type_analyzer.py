import dspy
from typing import List, Dict
from dspy.teleprompt import MIPROv2
from dspy.evaluate import Evaluate
from hyperon import MeTTa

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

def my_metric(example: dspy.Example, predictions: List[str]) -> float:
    sum = 0
    scnt = 0
    pcnt = 0
    metta = MeTTa()
    metta.run("!(bind! &kb (new-space))")
    for statement in example.statements:
        scnt += 1
        metta.run(f"!(add-atom &kb {statement})")
    for prediction in predictions:
        pcnt += 1
        try:
            pred = metta.parse_single(prediction).get_children()[2]
            res = metta.run(f"!(match &kb (: $typenamexzy123 {pred}) {pred})")
            if len(res[0]) != 0:
                sum += 1
        except:
            pass
    return sum / max(scnt, pcnt)



def create_training_data():
    return [
        dspy.Example(
            new_types=["(: Apple (-> (: $apple Object) Type))"],
            similar_types=["(: Fruit (-> (: $fruit Object) Type))", "(: Color (-> (: $c Object) Type))"],
            statements=["(: AppleIsFruit (-> (: $a (Apple $a)) (Fruit $a)))"]
        ),
        dspy.Example(
            new_types=["(: ToLeave (-> (: $person Object) (: $location Object) Type))"],
            similar_types=[
                "(: ToStay (-> (: $person Object) (: $location Object) Type))",
                "(: ToEat (-> (: $person Object) (: $food Object) Type))"  # Unrelated action
            ],
            statements=[
                "(: ToLeaveToNotToStay (-> (: $l (ToLeave $a $b)) (Not (ToLeave $a $b))))",
                "(: ToStayToNotToLeave (-> (: $t (ToStay $a $b)) (Not (ToStay $a $b))))"
            ]
        ),
        dspy.Example(
            new_types=["(: EntityType (-> (: $entity Object) Type))"],
            similar_types=[
                "(: Person EntityType)", 
                "(: Animal EntityType)",
                "(: Database (-> (: $db Object) Type))"  # Unrelated type
            ],
            statements=[
                "(: EntityTypeIsType (-> (: $e EntityType) Type))",
                "(: PersonIsEntityType (-> (: $p Person) (EntityType $p)))",
                "(: AnimalIsEntityType (-> (: $a Animal) (EntityType $a)))"
            ]
        ),
        # Example with no meaningful relationships
        dspy.Example(
            new_types=["(: Temperature (-> (: $t Number) Type))"],
            similar_types=[
                "(: Pressure (-> (: $p Number) Type))",
                "(: Distance (-> (: $d Number) Type))"
            ],
            statements=[]  # Empty because these types aren't meaningfully related
        ),
        dspy.Example(
            new_types=["(: HasLocation (-> (: $entity EntityType) (: $location Object) Type))"],
            similar_types=[
                "(: IsAt (-> (: $thing Object) (: $place Object) Type))",
                "(: HasColor (-> (: $obj Object) (: $color Object) Type))"  # Unrelated property
            ],
            statements=[
                "(: HasLocationToIsAt (-> (: $h (HasLocation $e $l)) (IsAt $e $l)))",
                "(: IsAtToHasLocation (-> (: $i (IsAt $e $l)) (HasLocation $e $l)))"
            ]
        ),
        dspy.Example(
            new_types=["(: Vehicle (-> (: $v Object) Type))", "(: Car (-> (: $c Object) Type))"],
            similar_types=[
                "(: Bicycle (-> (: $b Object) Type))",
                "(: Book (-> (: $bk Object) Type))",      # Unrelated type
                "(: Furniture (-> (: $f Object) Type))"   # Unrelated type
            ],
            statements=[
                "(: CarIsVehicle (-> (: $c (Car $c)) (Vehicle $c)))",
                "(: BicycleIsVehicle (-> (: $b (Bicycle $b)) (Vehicle $b)))"
            ]
        )
    ]

def optimize_prompt():
    # Initialize DSPy settings
    lm = dspy.OpenAI(model='gpt-4o-mini')
    dspy.settings.configure(lm=lm)
    
    # Create training data
    trainset = create_training_data()
    
    # Create the base program
    program = TypeAnalyzer()
    
    # Set up evaluation
    evaluate = Evaluate(devset=trainset, metric=my_metric)
    
    # Initialize MIPROv2 optimizer with light optimization settings
    teleprompter = MIPROv2(
        metric=my_metric,
        auto="light",  # Light optimization run
        num_threads=4,
        max_bootstrapped_demos=3,
        max_labeled_demos=4,
        verbose=True
    )
    
    # Optimize the program
    print("Optimizing program with MIPROv2...")
    optimized_program = teleprompter.compile(
        program.deepcopy(),
        trainset=trainset,
        num_trials=15,
        minibatch_size=25,
        minibatch=True,
        requires_permission_to_run=False
    )
    
    # Evaluate the optimized program
    score = evaluate(optimized_program)
    print(f"Optimized program score: {score}")
    
    # Save the optimized program
    optimized_program.save("mipro_optimized_type_analyzer")
    
    return optimized_program

def main():
    optimize_prompt()


if __name__ == "__main__":
    main()

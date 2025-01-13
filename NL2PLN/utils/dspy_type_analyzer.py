import dspy
from typing import List, Dict
from dspy.teleprompt import MIPROv2
from dspy.evaluate import Evaluate
from hyperon import MeTTa

class TypeAnalyzerSignature(dspy.Signature):
    """Generate logical linking statements between MeTTa types.
    
    Analyzes new types and similar existing types to generate valid MeTTa statements
    that express relationships between them using operators like -> and Not.
    """
    
    new_types: list[str] = dspy.InputField(desc="List of new type definitions in MeTTa syntax")
    similar_types: list[str] = dspy.InputField(desc="List of existing similar type definitions")
    statements: list[str] = dspy.OutputField(desc="Generated MeTTa statements expressing relationships between types")

class TypeAnalyzer(dspy.Module):
    def __init__(self):
        super().__init__()
        self.analyze = dspy.Predict(TypeAnalyzerSignature)
    
    def forward(self, new_types: List[str], similar_types: List[str]):
        prediction = self.analyze(new_types="\n".join(new_types), 
                                similar_types="\n".join(similar_types))
        return prediction

def my_metric(example: dspy.Example, prediction: dspy.Prediction, trace=None) -> float:
    sum = 0
    scnt = 0
    pcnt = 0
    metta = MeTTa()
    metta.run("!(bind! &kb (new-space))")
    for statement in example.statements:
        scnt += 1
        metta.run(f"!(add-atom &kb {statement})")
    for ps in prediction.statements:
        pcnt += 1
        try:
            pred = metta.parse_single(ps).get_children()[2]
            res = metta.run(f"!(match &kb (: $typenamexzy123 {pred}) {pred})")
            if len(res[0]) != 0:
                sum += 1
        except:
            pass

    maxcnt = max(scnt, pcnt)
    if maxcnt == 0:
        return 0.0
    return sum / maxcnt



def create_training_data():
    examples = [
        dspy.Example(
            new_types=["(: Apple (-> (: $apple Object) Type))"],
            similar_types=["(: Fruit (-> (: $fruit Object) Type))", "(: Color (-> (: $color Object) Type))"],
            statements=["(: AppleIsFruit (-> (: $apple_prf (Apple $apple_obj)) (Fruit $apple_obj)))"]
        ),
        dspy.Example(
            new_types=["(: ToLeave (-> (: $person Object) (: $location Object) Type))"],
            similar_types=[
                "(: ToStay (-> (: $person Object) (: $location Object) Type))",
                "(: ToEat (-> (: $person Object) (: $food Object) Type))"  # Unrelated action
            ],
            statements=[
                "(: ToLeaveToNotToStay (-> (: $leave_prf (ToLeave $person_obj $location_obj)) (Not (ToStay $person_obj $location_obj))))",
                "(: ToStayToNotToLeave (-> (: $stay_prf (ToStay $person_obj $location_obj)) (Not (ToLeave $person_obj $location_obj))))"
            ]
        ),
        # Example with no meaningful relationships
        dspy.Example(
            new_types=["(: Temperature (-> (: $t Object) Type))"],
            similar_types=[
                "(: Pressure (-> (: $p Object) Type))",
                "(: Distance (-> (: $d Object) Type))"
            ],
            statements=[]  # Empty because these types aren't meaningfully related
        ),
        dspy.Example(
            new_types=["(: Boy (-> (: $boy Object) Type))"],
            similar_types=[
                "(: Male (-> (: $male Object) Type))",
                "(: Person (-> (: $person Object) Type))"
            ],
            statements=["(: BoyIsMale (-> (: $boy_prf (Boy $boy_obj)) (Male $boy_obj)))"] # Boy is male but not necessarily a person (might be an animal)
        ),
        dspy.Example(
            new_types=["(: HasLocation (-> (: $entity Object) (: $location Object) Type))"],
            similar_types=[
                "(: IsAt (-> (: $thing Object) (: $place Object) Type))",
                "(: HasColor (-> (: $obj Object) (: $color Object) Type))"  # Unrelated property
            ],
            statements=[
                "(: HasLocationToIsAt (-> (: $loc_prf (HasLocation $entity_obj $location_obj)) (IsAt $entity_obj $location_obj)))",
                "(: IsAtToHasLocation (-> (: $at_prf (IsAt $entity_obj $location_obj)) (HasLocation $entity_obj $location_obj)))"
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
                "(: CarIsVehicle (-> (: $car_prf (Car $car_obj)) (Vehicle $car_obj)))",
                "(: BicycleIsVehicle (-> (: $bike_prf (Bicycle $bike_obj)) (Vehicle $bike_obj)))"
            ]
        ),
        # Shape hierarchy example
        dspy.Example(
            new_types=[
                "(: Shape (-> (: $s Object) Type))",
                "(: Rectangle (-> (: $r Object) Type))",
                "(: Square (-> (: $sq Object) Type))"
            ],
            similar_types=[
                "(: Circle (-> (: $c Object) Type))",
                "(: Weight (-> (: $w Number) Type))",  # Unrelated measurement
                "(: Volume (-> (: $v Number) Type))"   # Unrelated measurement
            ],
            statements=[
                "(: RectangleIsShape (-> (: $rect_prf (Rectangle $rect_obj)) (Shape $rect_obj)))",
                "(: SquareIsShape (-> (: $sq_prf (Square $sq_obj)) (Shape $sq_obj)))",
                "(: SquareIsRectangle (-> (: $sq_prf (Square $sq_obj)) (Rectangle $sq_obj)))"
            ]
        ),
        # Profession and skill relationships
        dspy.Example(
            new_types=[
                "(: HasSkill (-> (: $person Object) (: $skill Object) Type))",
                "(: Profession (-> (: $p Object) Type))",
                "(: RequiresSkill (-> (: $prof Profession) (: $skill Object) Type))"
            ],
            similar_types=[
                "(: WorksAs (-> (: $person Object) (: $prof Object) Type))",
                "(: Hobby (-> (: $h Object) Type))",      # Unrelated activity
                "(: Language (-> (: $l Object) Type))"    # Unrelated attribute
            ],
            statements=[
                "(: ProfessionRequiresSkillImpliesHasSkill (-> (: $work_prf (WorksAs $person_obj $prof_obj)) (-> (: $req_prf (RequiresSkill $prof_obj $skill_obj)) (HasSkill $person_obj $skill_obj))))"
            ]
        ),
        # Food and ingredient relationships
        dspy.Example(
            new_types=[
                "(: Food (-> (: $f Object) Type))",
                "(: Ingredient (-> (: $i Object) Type))",
                "(: ContainsIngredient (-> (: $food Food) (: $ing Ingredient) Type))"
            ],
            similar_types=[
                "(: Recipe (-> (: $r Object) Type))",
                "(: Tool (-> (: $t Object) Type))",       # Unrelated kitchen item
                "(: CookingMethod (-> (: $m Object) Type))" # Unrelated cooking concept
            ],
            statements=[
                "(: IngredientIsFood (-> (: $ing_prf (Ingredient $ing_obj)) (Food $ing_obj)))"
            ]
        )
    ]
    
    # Set inputs for all examples
    return [ex.with_inputs("new_types", "similar_types") for ex in examples]

def optimize_prompt():
    # Initialize DSPy settings
    lm = dspy.LM('deepseek/deepseek-chat')
    #lm = dspy.LM('openrouter/microsoft/phi-4')
    dspy.configure(lm=lm)
    
    # Create training data
    trainset = create_training_data()
    
    # Create the base program
    program = TypeAnalyzer()
    
    # Set up evaluation
    evaluate = Evaluate(devset=trainset, metric=my_metric)
    
    # Initialize MIPROv2 optimizer with light optimization settings
    teleprompter = MIPROv2(
        metric=my_metric,
        auto="medium",  # light/medium/heavy optimization run
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
    optimized_program.save("mipro_optimized_type_analyzer.json")
    
    return optimized_program

def single_test_step():
    # Run a single step of TypeAnalyzer for testing
    analyzer = TypeAnalyzer()
    lm = dspy.LM('openai/gpt-4o-mini')
    dspy.configure(lm=lm)
    
    # Test case with new vehicle type and existing types
    new_types = ["(: Motorcycle (-> (: $m Object) Type))"]
    similar_types = [
        "(: Vehicle (-> (: $v Object) Type))",
        "(: Car (-> (: $c Object) Type))"
    ]
    
    print("Testing TypeAnalyzer with:")
    print("New types:", new_types)
    print("Similar types:", similar_types)
    
    results = analyzer(new_types=new_types, similar_types=similar_types)
    print("\nGenerated statements:")
    for stmt in results:
        print(stmt)


def main():
    optimize_prompt()

if __name__ == "__main__":
    main()

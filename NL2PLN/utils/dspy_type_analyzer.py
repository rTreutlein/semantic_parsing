import dspy
import os
from typing import List, Dict
from dspy.teleprompt import MIPROv2
from dspy.evaluate import Evaluate
from hyperon import MeTTa

class TypeAnalyzerSignature(dspy.Signature):
    """Generate logical linking statements between MeTTa types.
    
    Analyzes new types and similar existing types to generate valid MeTTa statements
    that express relationships between them using operators like -> and Not.

    Make sure that:
    - The conclusion has no unbound variables
     - Meaning if a variable appeas in the conclusion it must exist in the premises
      -  CORRECT (: CompletionToFinishes (: $complete_prf (Completes $student_obj $course_obj)) (Finishes $student_obj $course_obj))
      -  INCORRECT (: CompletionToDegree (: $complete_prf (Completes $student_obj $course_obj)) (HasDegree $student_obj $degree_obj))
       - The $degree_obj variable is unbound as it does not exist in the premises

    - Negations (Not) should ONLY be used between relationships predicates (predicates with 2 or more arguments)
     - CORRECT: (: ToStayToNotToLeave (-> (: $stay_prf (ToStay $person_obj $location_obj)) (Not (ToLeave $person_obj $location_obj))))
     - INCORRECT: (: CarnivorToNotHerbivor (-> (: $carn_prf (Carnivore $carn_obj)) (Not (Herbivore $carn_obj))))
     - Instead of negating types, express positive relationships:
       e.g., (: EatsMeatToCarnivore (-> (: $eat_prf (EatsMeat $animal_obj)) (Carnivore $animal_obj)))

    - Try to come up with counter examples before you submit your answer

    - Only use the types provided do not invent new ones

    - If something is only possible but not always true do not create the relationship
      only create the relationship that are always true
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


        metta = MeTTa()
        for statement in prediction.statements:

            try:
                metta.parse_single(statement)
                metta.run(f"!(add-atom &kb {statement})")
            except:
                pass

        res = metta.run("!(match &self (: $prf (-> (: $prf_a ($A $a)) (Not ($B $a)))) (: $prf (-> (: $prf_a ($A $a)) (Not ($B $a)))))")

        for elem in res[0]:
            for statement in prediction.statements:
                if elem == statement:
                    prediction.statements.remove(statement)

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
        return 1
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
        dspy.Example(
            new_types=["(: Temperature (-> (: $t Object) Type))"],
            similar_types=[
                "(: Pressure (-> (: $p Object) Type))",
                "(: Distance (-> (: $d Object) Type))"
            ],
            statements=[]
        ),
        dspy.Example(
            new_types=["(: Boy (-> (: $boy Object) Type))"],
            similar_types=[
                "(: Male (-> (: $male Object) Type))",
                "(: Person (-> (: $person Object) Type))"
            ],
            statements=[
                "(: BoyIsMale (-> (: $boy_prf (Boy $boy_obj)) (Male $boy_obj)))",
                "(: BoyIsPerson (-> (: $boy_prf (Boy $boy_obj)) (Person $boy_obj)))"
            ]
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
                "(: Weight (-> (: $w Object) Type))",  # Unrelated measurement
                "(: Volume (-> (: $v Object) Type))"   # Unrelated measurement
            ],
            statements=[
                "(: RectangleIsShape (-> (: $rect_prf (Rectangle $rect_obj)) (Shape $rect_obj)))",
                "(: SquareIsShape (-> (: $sq_prf (Square $sq_obj)) (Shape $sq_obj)))",
                "(: SquareIsRectangle (-> (: $sq_prf (Square $sq_obj)) (Rectangle $sq_obj)))",
                "(: CircleIsShape (-> (: $circle_prf (Circle $circle_obj)) (Shape $circle_obj)))"
            ]
        ),
        # Profession and skill relationships
        dspy.Example(
            new_types=[
                "(: HasSkill (-> (: $person Object) (: $skill Object) Type))",
                "(: Profession (-> (: $p Object) Type))",
                "(: RequiresSkill (-> (: $prof Object) (: $skill Object) Type))"
            ],
            similar_types=[
                "(: WorksAs (-> (: $person Object) (: $prof Object) Type))",
                "(: Hobby (-> (: $h Object) Type))",      # Unrelated activity
                "(: Language (-> (: $l Object) Type))"    # Unrelated attribute
            ],
            statements=[
                "(: ProfessionRequiresSkillImpliesHasSkill (-> (: $work_prf (WorksAs $person_obj $prof_obj)) (: $req_prf (RequiresSkill $prof_obj $skill_obj)) (HasSkill $person_obj $skill_obj)))"
            ]
        ),
        # Food and ingredient relationships
        dspy.Example(
            new_types=[
                "(: Food (-> (: $f Object) Type))",
                "(: CookingIngredient (-> (: $i Object) Type))",
                "(: ContainsIngredient (-> (: $mixture Object) (: $ingredient Object) Type))"
            ],
            similar_types=[
                "(: Recipe (-> (: $r Object) Type))",
                "(: Tool (-> (: $t Object) Type))",       # Unrelated kitchen item
                "(: CookingMethod (-> (: $m Object) Type))" # Unrelated cooking concept
            ],
            statements=[
                "(: IngredientIsFood (-> (: $ing_prf (CookingIngredient $ing_obj)) (Food $ing_obj)))"
            ]
        ),
        # Time relationships
        dspy.Example(
            new_types=[
                "(: TimePoint (-> (: $t Object) Type))",
                "(: Before (-> (: $t1 Object) (: $t2 Object) Type))",
                "(: After (-> (: $t1 Object) (: $t2 Object) Type))"
            ],
            similar_types=[
                "(: Duration (-> (: $d Object) Type))",
                "(: Simultaneous (-> (: $t1 Object) (: $t2 Object) Type))"
            ],
            statements=[
                "(: BeforeToAfter (-> (: $before_prf (Before $time1_obj $time2_obj)) (After $time2_obj $time1_obj)))",
                "(: AfterToBefore (-> (: $after_prf (After $time1_obj $time2_obj)) (Before $time2_obj $time1_obj)))",
                "(: BeforToNotSimultaneous (-> (: $before_prf (Before $t1_obj $t2_obj)) (Not (Simultaneous $t1_obj $t2_obj))))",
                "(: AfterToNotSimultaneous (-> (: $after_prf (After $t1_obj $t2_obj)) (Not (Simultaneous $t1_obj $t2_obj))))",
                "(: SimultaneousToNotBefore (-> (: $sim_prf (Simultaneous $t1_obj $t2_obj)) (Not (Before $t1_obj $t2_obj))))",
                "(: SimultaneousToNotAfter (-> (: $sim_prf (Simultaneous $t1_obj $t2_obj)) (Not (After $t1_obj $t2_obj))))"
            ]
        ),
        # Animal classification
        dspy.Example(
            new_types=[
                "(: Animal (-> (: $a Object) Type))",
                "(: Mammal (-> (: $m Object) Type))",
                "(: Carnivore (-> (: $c Object) Type))",
                "(: Herbivore (-> (: $h Object) Type))"
            ],
            similar_types=[
                "(: Vertebrate (-> (: $v Object) Type))",
                "(: EatsPlants (-> (: $animal Object) Type))",
                "(: EatsMeat (-> (: $animal Object) Type))"
            ],
            statements=[
                "(: MammalIsAnimal (-> (: $mammal_prf (Mammal $mammal_obj)) (Animal $mammal_obj)))",
                "(: CarnivoreEatsMeat (-> (: $carn_prf (Carnivore $carn_obj)) (EatsMeat $carn_obj)))",
                "(: HerbivoreEatsPlants (-> (: $herb_prf (Herbivore $herb_obj)) (EatsPlants $herb_obj)))",
            ]
        ),
        # Weather conditions
        dspy.Example(
            new_types=[
                "(: WeatherCondition (-> (: $w Object) Type))",
                "(: Raining (-> (: $r Object) Type))",
                "(: Sunny (-> (: $s Object) Type))",
                "(: Cloudy (-> (: $c Object) Type))"
            ],
            similar_types=[
                "(: Temperature (-> (: $t Object) Type))",
                "(: Humidity (-> (: $h Object) Type))"
            ],
            statements=[
                "(: RainingIsWeather (-> (: $rain_prf (Raining $weather_obj)) (WeatherCondition $weather_obj)))",
                "(: SunnyIsWeather (-> (: $sun_prf (Sunny $weather_obj)) (WeatherCondition $weather_obj)))",
                "(: CloudyIsWeather (-> (: $cloud_prf (Cloudy $weather_obj)) (WeatherCondition $weather_obj)))",
            ]
        ),
        # Educational Achievement Chain
        dspy.Example(
            new_types=[
                "(: Studies (-> (: $student Object) (: $subject Object) Type))",
                "(: Completes (-> (: $student Object) (: $course Object) Type))",
                "(: HasDegree (-> (: $person Object) (: $degree Object) Type))",
                "(: QualifiedFor (-> (: $person Object) (: $position Object) Type))",
                "(: RequiresDegree (-> (: $position Object) (: $degree Object) Type))"
            ],
            similar_types=[
                "(: Enrolls (-> (: $student Object) (: $course Object) Type))",
                "(: Teaches (-> (: $teacher Object) (: $subject Object) Type))"
            ],
            statements=[
                "(: DegreeQualifiesPerson (-> (: $degree_prf (HasDegree $person_obj $degree_obj)) (: $req_prf (RequiresDegree $position_obj $degree_obj)) (QualifiedFor $person_obj $position_obj)))",
                '(: EnrollsToStudies (-> (: $enroll_prf (Enrolls $student_obj $course_obj)) (Studies $student_obj $course_obj)))',
                '(: CompletesToNotEnrolls (-> (: $complete_prf (Completes $student_obj $course_obj)) (Not (Enrolls $student_obj $course_obj))))',
            ]
        ),
        # Supply Chain Relationships
        dspy.Example(
            new_types=[
                "(: Produces (-> (: $manufacturer Object) (: $product Object) Type))",
                "(: Supplies (-> (: $supplier Object) (: $material Object) (: $manufacturer Object) Type))",
                "(: Uses (-> (: $product Object) (: $material Object) Type))",
                "(: RequiresMaterial (-> (: $manufacturer Object) (: $material Object) Type))"
            ],
            similar_types=[
                "(: Stores (-> (: $warehouse Object) (: $item Object) Type))",
                "(: Transports (-> (: $carrier Object) (: $cargo Object) Type))"
            ],
            statements=[
                "(: ProductionNeedsMaterial (-> (: $prod_prf (Produces $manuf_obj $product_obj)) (: $use_prf (Uses $product_obj $material_obj)) (RequiresMaterial $manuf_obj $material_obj)))",
                "(: SuppliesToRequiresMaterial (-> (: $supply_prf (Supplies $supplier_obj $material_obj $manuf_obj)) (RequiresMaterial $manuf_obj $material_obj)))"
            ]
        ),
    ]
    
    # Set inputs for all examples
    return [ex.with_inputs("new_types", "similar_types") for ex in examples]

def optimize_prompt(program,trainset,mode="light",out="mipro_optimized_type_analyzer"):
    # Set up evaluation
    evaluate = Evaluate(devset=trainset, metric=my_metric)
    
    # Initialize MIPROv2 optimizer with light optimization settings
    teleprompter = MIPROv2(
        metric=my_metric,
        auto=mode,  # light/medium/heavy optimization run
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
    optimized_program.save(f"{out}.json")
    
    return optimized_program

from pprint import pprint

def eval(program, dataset):
    print("\nRunning optimized program on training set and comparing results:")
    total = 0
    for example in dataset:
        # Get the optimized program's predictions
        prediction = program(new_types=example.new_types, 
                                     similar_types=example.similar_types)
        
        metric = my_metric(example, prediction, trace=None)
        total += metric

        if metric != 1.0:
            print(f"\nExample mismatch for types metric {metric}:")
            print(f"New types:")
            pprint(example.new_types)
            print(f"\nSimilar types:")
            pprint(example.similar_types)
            print(f"\nExpected statements:")
            pprint(example.statements, width=200)
            print(f"\nActual statements:")
            pprint(prediction.statements, width=200)
            print("="*80)
            
    print(f"\nTotal metric: {total/len(dataset)}")


def main():
    program = TypeAnalyzer()
    #lm = dspy.LM('deepseek/deepseek-chat', temperature=0.5)
    #lm = dspy.LM('openrouter/qwen/qwq-32b-preview', temperature=0.5, max_tokens=10000)
    #lm = dspy.LM('openai/o1-mini', temperature = 1, max_tokens = 5000)
    lm = dspy.LM('anthropic/claude-3-5-sonnet-20241022')
    dspy.configure(lm=lm)

    # Load the training set
    trainset = create_training_data()

    # Optimize the program
    #program = optimize_prompt(program,trainset,"medium")

    program.load("claude_optimized_type_analyzer.json")
    eval(program, trainset)
    

if __name__ == "__main__":
    main()

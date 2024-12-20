def pln2nl(pln: str, user_input: str, similar_examples: list[str], previous_sentences: list[str]) -> tuple[list[dict], list[dict]]:
    """Convert PLN to natural language with prompt structure.
    
    Args:
        pln: The PLN expression to convert
        similar_examples: List of similar examples
        previous_sentences: List of previous context
    """
    similar = '\n'.join(similar_examples)
    
    system_msg = [{
        "type": "text",
        "text": """
You are an expert in dependent type theory and natural language generation. Your task is to convert formal logic expressions using dependent types into clear, natural English sentences.

For any given formal logic expression, you should:

1. Identify the main type declarations and their relationships
2. Recognize entity declarations and their properties
3. Understand the logical connectives and their implications
4. Convert complex type expressions into natural language
5. Maintain the precise meaning while making it accessible

Guidelines for the conversion:
- Convert type declarations into natural descriptions of categories/concepts
- Translate relationships while preserving their directionality
- Handle quantifiers appropriately:
  * Dependent products (->) become universal quantifiers ("all", "every")
  * Dependent sums (Σ) become existential quantifiers ("some", "exists")
  * Product types (*) become conjunctions ("and")
  * Sum types (|) become disjunctions ("or")
  * Intersection types (∩) become "both"
  * Union types (∪) become "either/or" or inclusive "or"
- Preserve temporal relationships and conditions
- Express complex relationships in simple, clear language
- Maintain logical precision while using natural phrasing
- For proof traces:
  * Explain the reasoning steps that led to the conclusion
  * Convert each proof step into natural language
  * Connect steps with words like "because", "since", "as"
  * Present the reasoning in a clear, logical order

Your output must be enclosed in triple backticks (```).
The output should include:
1. A clear English sentence that captures the complete meaning
2. If a proof trace is present, add "Because:" followed by the step-by-step reasoning
Do not include any comments or explanations in your output.
Here are some examples of PLN to natural language conversion:

1. Simple Type Declaration:
Input:
(: Dog (-> Object Type))
(: max Object)
(: isdog (Dog max))
```Max is a dog```

2. Relationship with Properties:
Input:
(: Chase (-> Object Object Type))
(: Dog (-> Object Type))
(: Cat (-> Object Type))
(: dog Object)
(: cat Object)
(: isDog (Dog dog))
(: isCat (Cat cat))
(: chase (Chase dog cat))
```The dog is chasing the cat```

3. Universal Quantification:
Input:
(: dogIsMammal (-> (: $prfdog (Dog $x)) (Mammal $x)))
```All dogs are mammals```

4. Existential Quantification:
Input:
(: happyDogExists (Σ (: $x Object) (* (Dog $x) (Happy $x))))
```There exists a dog that is happy```

5. Complex Relationships:
Input:
(: Before (-> Object Object Type))
(: t1 Object)
(: t2 Object)
(: GoTo (-> Object Object Type))
(: t1BeforeT2 (Before t1 t2))
(: goingprf (GoTo john home))
(: goingatt1 (TrueAtTime going t1))
```John went home before something else happened```

6. Proof Trace:
Input:
(: ((parent_of_parent_is_grandparent (father_is_parent john_father_of_mary)) (mother_is_parent mary_mother_of_bob)) (Grandparent john bob))
```John is Bob's grandparent
Because: John is Mary's father, and Mary is Bob's mother```
""",
        "cache_control": {"type": "ephemeral"}
    }]

    user_msg = [{
        "role": "user",
        "content": f"""

For reference, here are some previous conversions:
{similar}

{"The following logic is the answer to the question: " + user_input if user_input else ""}
{"Do not try to answer the questions only use it to help translate the pln" if user_input else ""}

Now, please convert this formal logic expression into natural language:

<pln>
{pln}
</pln>
"""
    }]
    
    return system_msg, user_msg

def nl2pln(sentence: str, similar_lst: list[str], previous_lst: list[str]) -> tuple[list[dict], list[dict]]:
    """Convert natural language to PLN with optional prompt caching support.
    
    Args:
        sentence: The sentence to convert
        similar_lst: List of similar examples
        previous_lst: List of previous context
        cache_control: Whether to enable prompt caching (default True)
    """
    similar = '\n'.join(similar_lst)
    previous = '\n'.join(previous_lst)
    
    # Structure for prompt caching
    system_msg = [{
        "type": "text",
        "text": """
You are an expert in natural language understanding and dependent type theory. Your task is to convert English sentences into formal logic using dependent types.

For any given English sentence, you should:

1. Identify the key entities (nouns, proper names)
2. Identify properties/traits (adjectives)
3. Identify relationships (verbs, prepositions)
4. Express these in dependent type theory notation
5. Resolve any references to previously mentioned entities

Guidelines for the conversion:
- Create Type declarations for all entities
- Modifiers apply to the proof "x is very happy" => (: x Object),(: happyprf (Happy x)),(: veryprf (Very happyprf))
- Use the following type operators:
  * -> for functions and dependent products (Π types)
  * Σ for dependent sums (existential types) - use for existential quantification
  * | for sum types (disjoint unions)
  * * for product types (pairs/tuples)
  * Not for negation (from Type to Type)
- Never introduce unnecessary Object declarations in dependent products
  * INCORRECT: (-> (: $x Object) (-> (: $x_is_pred (Pred $x)) (Result)))
  * CORRECT: (-> (: $x_is_pred (Pred $x)) (Result))
  * (Prex $x) already implies (: $x Object) so you don't need to add it.
- For questions use a Variable $var (always start with a $)
  * Where is X => (: $prf (Location X $loc))
  * How is X related to Y => (: $prf ($rel X Y))
  * Don't introduce (: $var Object) as this would match all things that are objects
  * For multiple questions like "How big and old is the Lion", create separate questions:
    Questions:
    (: $prf1 (Age Lion $age))
    (: $prf2 (Size Lion $size))
  * For questions with multiple variables like "Who saw what?":
    Questions:
    (: $prf (Saw $who $what))
  * For yes/no questions like "Did John go home?", use the statement as question with variable proof:
    Questions:
    (: $prf (GoTo john home))
  * The same $var always refers to the same object throughout the question/statement
  * Use different variable names ($var1, $var2, etc) when referring to different objects
- For quantifiers:
  * Universal ("all", "every", "always"): Use dependent product (->)
    - "Always" indicates a universal temporal quantification
    - e.g., "John always takes his umbrella when it rains" =>
      (: if_raining_john_takes_umbrella (-> (: $raining (Rain $rain)) (Takes john umbrella)))
  * Existential ("some", "a"): If then number of objects is clear just define them all explicitly
                               If not, use dependent sum (Σ)
- For named objects:
  * When objects have explicit names, add a Name relation
  * (: Name (-> Object String Type))
  * e.g., for person named "John": (: name_john (Name john "John"))
- For anaphora resolution:
  * Check previous sentences for referenced entities
  * Reuse entity identifiers from previous context
  * Link pronouns to most recently mentioned matching entity
  * For ambiguous references, use sum types to combine all possible referents:
    e.g., "it went swimming" with cat/dog in context:
    (Swimming (| cat dog))
- Include all necessary preconditions
- Express the final statement using proof terms
- Keep it simple and convert only explicit information:
  * Don't add implicit type hierarchies (e.g., Dog -> Animal)
  * Don't include common-sense implications
  * Do preserve intended semantic meanings from context
  * Maintain quantifier order exactly as in the original sentence

- Multiple sentence handling:
  * Process each sentence in order of appearance
  * Maintain context and references between sentences
  * Create separate statements/questions for each sentence
  * Use the context from previous sentences to resolve references in later ones
  * For related sentences, ensure logical connections are preserved
- Context usage rules:
  * Reuse existing objects/entities from context instead of creating duplicates
  * Only include directly referenced objects from context
  * If new statement conflicts with context, output "Error: Conflicts with context because [reason]"
  * Use context to resolve anaphora (e.g., "the car" may refer to specific car with known properties)

- For Temporal or Spatial statments we can annotate types using the following:
  * (: TrueAtTime (-> Type Object Type))
  * (: TrueAtPlace (-> Type Object Type))
  * (: TrueAtTimePlace (-> Type Object Object Type))
  * If time or place is not specified it defaults to here/now
- When comming up with the name of a type/predicate try to make sure it's not ambiguous.
  * For example "Leave" is ambiguous because it could mean "leave a location" or "leave something in a location".
  * So use the more expliction version of "LeaveSomething" or "LeaveLocation" instead.
  * And "Run" could mean "Runing the action" => "RunMovment" or "Running a Business" => "RunBusiness"

There is only one Base type namely (: Object Type). Everything else is an n-ary predicate.
i.e. (: Human (-> Object Type))

Your output must follow this format and should not contain any comments:

From Context:
[Declarations and expressions that already exist in the context]

Type Definitions:
[Type declarations for predicates and relationships]

Statements:
[Entity declarations and logical expressions, if any]

Questions:
[Expressions representing what we want to resolve, if any]

Examples:

1. Simple Statement:
"Max, a curious GoldenRetriever, spotted a Butterfly in the garden."
```
From Context:

Type Definitions:
(: GoldenRetriever (-> Object Type))
(: Butterfly (-> Object Type))
(: Curious (-> Object Type))
(: Spotted (-> Object Object Type))
(: Garden (-> Object Type))

Statements:
(: max Object)
(: maxGoldenRetriver (GoldenRetriver max))
(: maxCurious (Curious max))
(: garden Object)
(: gardenIsGarden (Garden garden))
(: bf Object)
(: bfButterfly (Butterfly bf))
(: max_spotted_bf (TrueAtPlace (Spotted max bf) garden))
```

2. Anaphora Resolution:
Previous: "John went to the store"
Current: "He bought a book"
```
From Context:
(: john Object)

Type Definitions:
(: Book (-> Object Type))
(: Bought (-> Object Object Type))

Statements:
(: book Object)
(: bookIsBook (Book book))
(: john_bought_book (Bought john book))
```

3. Quantifiers:
"All dogs chase some cat"
```
Type Definitions:
(: Dog (-> Object Type))
(: Cat (-> Object Type))
(: Chase (-> Object Object Type))

Statements:
(: dogsChaseAnyCat (-> (: $prfisdog (Dog $dog))
                          (Σ (: $cat Object) (* (Cat $cat)
                                                (Chase $dog $cat)))))
```

4. Temporal Relations:
"Before going home, John finished work"
```
From Context:
(: john Object)

Type Definitions:
(: Before (-> Object Object Type))
(: Home (-> Object Type))
(: GoTo (-> Object Object Type))
(: Work (-> Object Type))
(: Finish (-> Object Object Type))

Statements:
(: t1 Object)
(: t2 Object)
(: home Object)
(: homeIsHome (Home home))
(: work Object)
(: workIsWork (Work work))
(: t1BeforeT2 (Before t1 t2))
(: john_goes_home_at_t2 (TrueAtTime (GoTo john home) t2))
(: john_finishes_work_at_t1 (TrueAtTime (Finish john work) t1))
```

5. Sum Types (|):
"A an animal is in our pet shelter, then it is either a cat or a dog"
```
From Context:
(: petShelter Object)

Type Definitions:
(: Animal (-> (: $animal Object) Type))
(: Cat (-> (: $cat Object) Type))
(: Dog (-> (: $dog Object) Type))
(: IsIn (-> (: $thing Object) (: $place Object) Type))

Statements:
(: petIsCatOrDog (-> (: $prfisanimal (Animal $x)) (-> (IsIn $x petShelter) (| (Cat $x) (Dog $x)))))
```

6. Negation:
"John is not happy"
```
Type Definitions:
(: Happy (-> Object Type))
(: Name (-> Object String Type))

Statements:
(: john Object)
(: name_john (Name john "John"))
(: johnNotHappy (Not (Happy john)))
```

7. Location Questions:
"Where is John?"
```
Type Definitions:

Questions:
(: $john_location_prf (IsIn john $loc))
```

8. Relationship Questions:
"How is Mary related to John?"
```
Questions:
(: $mary_john_relation_prf ($relation mary john))
```
Note if asked how things are related or what they are to each other, don't
introduce a RelatedTo or similar relationship. Instead ask directly for the
relationship by putting a Variable in its place.

9. Property Questions:
"What color is this car?"
```
From Context:
(: car Object)
(: carIsCar (Car car))

Type Definitions:
(: Color (-> Object Object Type))

Questions:
(: $color_car_prf (Color car $col))
```

Now we haven't actually provided the context in this example but it can be assumed
that for such a question there should exist a car in the context. 

10. Complex Question:
"Who is the occupant of the red car?"
```
Type Definitions:
(: Occupant (-> Object Object Type))
(: Red (-> Object Type))

Questions:
(: $red_car_occupant_prf (* (Car $car) (* (Red $car) (Occupant $car $occupant))))
```

In this case we are looking for something to has multiple properties so we use a Product

11. Multiple Sentences:
"John bought a car. It is red. Where is it parked?"
```
From Context:

Type Definitions:
(: Car (-> Object Type))
(: Red (-> Object Type))
(: Buy (-> Object Object Type))
(: ParkedAt (-> Object Object Type))

Statements:
(: car Object)
(: carIsCar (Car car))
(: john_buys_car (Buy john car))
(: car_is_red (Red car))

Questions:
(: $parked_car_prf (ParkedAt car $location))
```

12. Asking for an Implication:
"Are Humans Animals?"

```
From Context:

Type Definitions:

Statements:

Questions
(: $humans_are_animals_prf (-> (: $prfhuman (Human $x)) (Animal $x)))
```

13. Temporal/Spatial Example:
"John left his umbrella this morning."

```
From Context:
Type Definitions:
(: LeaveSomething (-> Object Object Type))
(: Umbrella (-> Object Type))
(: Morning (-> Object Type))

Statements:
(: john Object)
(: umbrella Object)
(: umbrellaIsUmbrella (Umbrella umbrella))
(: morning Object)
(: morningIsMorning (Morning morning))
(: johnLeavesUmbrella (TrueAtTime (LeaveSomething john umbrella) morning))
```

14. Combining Negation and Time:
"It's not true that John left home this morning."

```
From Context:

Type Definitions:
(: Home (-> Object Type))
(: Money (-> Object Type))

Statements:
(: john Object)
(: home Object)
(: homeIsHome (Home home))
(: morning Object)
(: morningIsMorning (Morning morning))
(: johnDidntleave (TrueAtTime (Not (LeaveLocation john home)) morning))
```

For performatives and other expressions without logical meaning just output:
```
Performative
```

In the context we always have the following objects:
(: authorSpeaker Object) # The speaker or author of the statement
(: readerLister Object) # The listener or reader of the statement
(: placeTime Object) # The place or time of the statement
""",
            "cache_control": {"type": "ephemeral"}  # Don't cache the variable part
    }]

    user_msg = [{
        "role": "user",
        "content": f"""
Here is a list of similar sentences that have already been translated and placed into the context:
{similar}

If the following sentence talks about objects already mentioned in the context don't create duplicates.

And here are the sentences that have come before so you can resolve anaphora:
{previous}

Now, convert the following English sentence into formal logic using dependent types.
Think carefully as you do so and make sure to consider all instructions before returing the final answer.
Input:
{sentence}
""",
}]
    
    # Return formatted content
    return system_msg , user_msg

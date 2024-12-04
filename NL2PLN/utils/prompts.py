def pln2nl(pln: str, user_input: str, similar_examples: list[str], previous_sentences: list[str]):
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

Your output must be enclosed in triple backticks (```).
The output should be a single, clear English sentence that captures the complete meaning.
Do not include any comments or explanations in your output.
Here are some examples of PLN to natural language conversion:

1. Simple Type Declaration:
Input:
(: Dog (-> Object Object Type))
(: max Object)
(: dogrel Object)
(: isdog (Dog dogrel max))
```Max is a dog```

2. Relationship with Properties:
Input:
(: Chase (-> Object Object Object Type))
(: Dog (-> Object Object Type))
(: Cat (-> Object Object Type))
(: chase Object)
(: dog Object)
(: cat Object)
(: dogrel Object)
(: catrel Object)
(: isDog (Dog dogrel dog))
(: isCat (Cat catrel cat))
(: prf1 (Chase chase dog cat))
```The dog is chasing the cat```

3. Universal Quantification:
Input:
(: prf1 (-> (Dog $dogrel x) (Σ (: $mammalrel Object) (Mammal $mammalrel x))))
```All dogs are mammals```

4. Existential Quantification:
Input:
(: prf1 (Σ (: x Object) (* (Dog dogrel x) (Happy happyrel x))))
```There exists a dog that is happy```

5. Complex Relationships:
Input:
(: Before (-> Object Object Object Type))
(: t1 Object)
(: t2 Object)
(: GoTo (-> Object Object Object Type))
(: beforerel Object)
(: prf1 (Before beforerel t1 t2))
(: going Object)
(: prf2 (GoTo going john home))
(: timrel Object)
(: goingatt1 (AtTime timerel going t1))
```John went home before something else happened```
""",
        "cache_control": {"type": "ephemeral"}
    }]

    user_msg = [{
        "role": "user",
        "content": f"""

For reference, here are some previous conversions:
{similar}

{"The following logic is the answer to the question: " + user_input if user_input else ""}

Now, please convert this formal logic expression into natural language:

<pln>
{pln}
</pln>
"""
    }]
    
    return system_msg, user_msg

def nl2pln(sentence: str, similar_lst: list[str], previous_lst: list[str]):
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
- All predicates and relationships require a relationship object:
  * Single predicates: (Happy happyrel obj)
  * Binary relations: (Chase chaserel obj1 obj2)
  * Modifiers apply to relationship objects: (Very veryrel happyrel)
- Use the following type operators:
  * -> for functions and dependent products (Π types)
  * Σ for dependent sums (existential types) - use for existential quantification
  * | for sum types (disjoint unions)
  * * for product types (pairs/tuples)
  * Not for negation (from Type to Type)
- For questions use a Variable $var (always start with a $)
  * Where is X => (: $prf (Location X $loc))
  * How is X related to Y => (: $prf ($rel X Y))
  * Don't introduce (: $var Object) as this would match all things that are objects
  * For multiple questions like "Where and when did John go?", create separate questions:
    Questions:
    (: $prf1 (Location $relobj1 john $loc))
    (: $prf2 (Time $relobj2 john $time))
  * For questions with multiple variables like "Who saw what?":
    Questions:
    (: $prf (Saw $relobj $who $what))
  * For yes/no questions like "Did John go home?", use the statement as question with variable proof:
    Questions:
    (: $prf (GoTo going john home))
  * The same $var always refers to the same object throughout the question/statement
  * Use different variable names ($var1, $var2, etc) when referring to different objects
- For quantifiers:
  * Universal ("all", "every"): Use dependent product (->)
  * Existential ("some", "a"): If then number of objects is clear just define them all explicitly
                               If not, use dependent sum (Σ)
- For anaphora resolution:
  * Check previous sentences for referenced entities
  * Reuse entity identifiers from previous context
  * Link pronouns to most recently mentioned matching entity
  * For ambiguous references, use sum types to combine all possible referents:
    e.g., "it went swimming" with cat/dog in context:
    (Swimming swimrel (| (Cat catrel cat) (Dog dogrel dog)))
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
"Max, a curious GoldenRetriver, spotted a Butterfly in the garden."
```
From Context:

Type Definitions:
(: GoldenRetriver (-> Object Object Type))
(: Butterfly (-> Object Object Type))
(: Curious (-> Object Object Type))
(: Spotted (-> Object Object Object Type))
(: Garden (-> Object Object Type))
(: In (-> Object Object Object Type))

Statements:
(: max Object)
(: garden Object)
(: gardenrel Object)
(: retriverrel Object)
(: curiousrel Object)
(: maxGoldenRetriver (GoldenRetriver retriverrel max))
(: maxCurious (Curious curiousrel max))
(: gardenIsGarden (Garden gardenrel garden))
(: bf Object)
(: butttvrel Object)
(: bfButterfly (Butterfly butttvrel bf))
(: spot Object)
(: spottedrel Object)
(: prf1 (Spotted spottedrel max bf))
(: inrel Object)
(: prf2 (In inrel bf garden))
```

2. Anaphora Resolution:
Previous: "John went to the store"
Current: "He bought a book"
```
From Context:
(: john Object)

Type Definitions:
(: Book (-> Object Object Type))
(: Bought (-> Object Object Object Type))

Statements:
(: book Object)
(: bookrel Object)
(: bookIsBook (Book bookrel book))
(: purchase Object)
(: prf2 (Bought purchase john book))
```

3. Quantifiers:
"All dogs chase some cat"
```
Type Definitions:
(: Dog (-> Object Object Type))
(: Cat (-> Object Object Type))
(: Chase (-> Object Object Object Type))

Statements:
(: prf1 (-> (Dog $dogrle $dog)
           (Σ (: $catrel Object) 
              (Σ (: $cat Object) 
                 (* (Cat $catrel $cat)
                    (Σ (: $chaserel Object)
                       (Chase $chaserel $dog $cat))))))
```

4. Temporal Relations:
"Before going home, John finished work"
```
From Context:
(: john Object)

Type Definitions:
(: TimePoint (-> Object Object Type))
(: Before (-> Object Object Object Type))
(: Home (-> Object Object Type))
(: AtTime (-> Object Object Object Type))
(: GoTo (-> Object Object Object Type))
(: Work (-> Object Object Type))
(: Finish (-> Object Object Object Type))

Statements:
(: t1 Object)
(: t2 Object)
(: tprel1 Object)
(: tprel2 Object)
(: t1IsTime (TimePoint tprel1 t1))
(: t2IsTime (TimePoint tprel2 t2))
(: home Object)
(: homerel Object)
(: homeIsHome (Home homerel home))
(: work Object)
(: workrel Object)
(: workIsWork (Work workrel work))
(: beforerel Object)
(: prf1 (Before beforerel t1 t2))
(: going Object)
(: finishing Object)
(: prf2 (GoTo going john home))
(: prf3 (AtTime going t1))
(: prf4 (Finish finishing john work))
(: prf5 (AtTime finishing t2))
```

5. Sum Types (|):
"A pet is either a cat or a dog"
```
Type Definitions:
(: Pet (-> Object Object Type))
(: Cat (-> Object Object Type))
(: Dog (-> Object Object Type))

Statements:
(: prf1 (-> (Pet $petrel $x) (| (Σ (: $catrel Object) (Cat $catrel $x)) (Σ (: $dogrel Object) (Dog $dogrel $x)))))
```

6. Negation:
"John is not happy"
```
Type Definitions:
(: Happy (-> Object Object Type))

Statements:
(: happyrel Object)
(: prf1 (Not (Happy happyrel john)))
```

6. Location Questions:
"Where is John?"
```
Type Definitions:
(: Location (-> Object Object Object Type))

Questions:
(: $prf (Location $locrel john $loc))
```

7. Relationship Questions:
"How is Mary related to John?"
```
Questions:
(: $prf ($rel $relobj mary john))
```
Note if asked how things are related or what they are to each other, don't
introduce a RelatedTo or similar relationship. Instead ask directly for the
relationship by putting a Variable in its place.

8. Property Questions:
"What color is this car?"
```
From Context:
(: car Object)
(: carrel Object)
(: carIsCar (Car carrel car))

Type Definitions:
(: Color (-> Object Object Object Type))

Questions:
(: $prf (Color $colorrel car $col))
```

Now we haven't actually provided the context in this example but it can be assumed
that for such a question there should exist a car in the context. 

9. Complex Question:
"Who is the occupant of the red car?"
```
Type Definitions:
(: Occupant (-> Object Object Object Type))
(: Red (-> Object Object Type))

Questions:
(: $prf (* (Car $carrel $car) (* (Red $redrel $car) (Occupant $occupantrel $car $occupant))))
```

In this case we are looking for something to has multiple properties so we use a Product

10. Multiple Sentences:
"John bought a car. It is red. Where is it parked?"
```
From Context:

Type Definitions:
(: Car (-> Object Object Type))
(: Red (-> Object Object Type))
(: Buy (-> Object Object Object Type))
(: ParkedAt (-> Object Object Object Type))

Statements:
(: car Object)
(: carrel Object)
(: carIsCar (Car carrel car))
(: buying Object)
(: prf1 (Buy buying john car))
(: redrel Object)
(: prf2 (Red redrel car))

Questions:
(: $prf (ParkedAt $relobj car $location))
```

For performatives and other expressions without logical meaning just output:
```
Performative
```

In the context we always have the following objects:
(: authorSpeaker Object)
(: readerLister Object)
(: placeTime Object)
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

Now, convert the following English sentence into formal logic using dependent types:
{sentence}
""",
}]
    
    # Return formatted content
    return system_msg , user_msg

def pln2nl(pln: str, similar_examples: list[str], previous_sentences: list[str]):
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
Here are some examples of PLN to natural language conversion:

1. Simple Type Declaration:
Input:
(: Dog (-> Object Type))
(: max Object)
(: isdog (Dog max))
```Max is a dog```

2. Relationship with Properties:
Input:
(: Chase (-> Object Object Object Type))
(: Dog (-> Object Type))
(: Cat (-> Object Type))
(: chase Object)
(: dog Object)
(: cat Object)
(: prf1 (Chase chase dog cat))
```The dog is chasing the cat```

3. Universal Quantification:
Input:
(: prf1 (-> (Dog x) (Mammal x)))
```All dogs are mammals```

4. Existential Quantification:
Input:
(: prf1 (Σ (: x Object) (* (Dog x) (Happy x))))
```There exists a dog that is happy```

5. Complex Relationships:
Input:
(: Before (-> Object Object Type))
(: t1 Object)
(: t2 Object)
(: GoTo (-> Object Object Object Type))
(: prf1 (Before t1 t2))
(: going Object)
(: prf2 (GoTo going john home))
```John went home before something else happened```
""",
        "cache_control": {"type": "ephemeral"}
    }]

    user_msg = [{
        "role": "user",
        "content": f"""

For reference, here are some previous conversions:
{similar}

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

Your output must follow this format:

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
(: GoldenRetriver (-> Object Type))
(: Butterfly (-> Object Type))
(: Curious (-> Object Type))
(: Spotted (-> Object Object Object Type))
(: Garden (-> Object Type))
(: In (-> Object Object Type))

Statements:
(: max Object)
(: garden Object)
(: maxGoldenRetriver (GoldenRetriver max))
(: maxCurious (Curious max))
(: gardenIsGarden (Garden garden))
(: bf Object)
(: bfButterfly (Butterfly bf))
(: spot Object)
(: prf1 (Spotted spot max bf))
(: prf2 (In bf garden))
```

2. Anaphora Resolution:
Previous: "John went to the store"
Current: "He bought a book"
```
From Context:
(: john Object)

Type Definitions:
(: Book (-> Object Type))
(: Bought (-> Object Object Object Type))

Statements:
(: book Object)
(: bookIsBook (Book book))
(: purchase Object)
(: prf2 (Bought purchase john book))
```

3. Quantifiers:
"All dogs chase some cat"
```
Type Definitions:
(: Dog (-> Object Type))
(: Cat (-> Object Type))
(: Chase (-> Object Object Object Type))
(: AtTime (-> Object Object Type))

Statements:
(: prf1 (-> (Dog x)
           (Σ (: $y Object) 
              (* (Cat $y)
                 (Σ (: $c Object) 
                    (Chase $c x $y))))))
```

4. Temporal Relations:
"Before going home, John finished work"
```
Type Definitions:
(: TimePoint (-> Object Type))
(: Before (-> Object Object Type))
(: Home (-> Object Type))
(: GoTo (-> Object Object Object Type))
(: Work (-> Object Type))
(: Finish (-> Object Object Object Type))

Statements:
(: t1 Object)
(: t2 Object)
(: t1IsTime (TimePoint t1))
(: t2IsTime (TimePoint t2))
(: home Object)
(: homeIsHome (Home home))
(: work Object)
(: workIsWork (Work work))
(: prf1 (Before t1 t2))
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
(: Pet (-> Object Type))
(: Cat (-> Object Type))
(: Dog (-> Object Type))

Statements:
(: prf1 (-> (Pet x) (| (Cat x) (Dog x))))
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
(: $prf (Location $relobj john $loc))
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
(: carIsCar (Car car))

Type Definitions:
(: Color (-> Object Object Type))

Questions:
(: $prf (Color $relobj car $col))
```

Now we haven't actually provided the context in this example but it can be assumed
that for such a question there should exist a car in the context. 

9. Complex Question:
"Who is the occupant of the red car?"
```
Type Definitions:
(: Occupant (-> Object Object Object Type))
(: Red (-> Object Type))

Questions:
(: $prf (* (Car $car) (* (Red $car) (Occupant $relobj $car $occupant))))
```

In this case we are looking for something to has multiple properties so we use a Product

10. Multiple Sentences:
"John bought a car. It is red. Where is it parked?"
```
From Context:

Type Definitions:
(: Car (-> Object Type))
(: Red (-> Object Type))
(: Buy (-> Object Object Object Type))
(: ParkedAt (-> Object Object Object Type))

Statements:
(: car Object)
(: carIsCar (Car car))
(: buying Object)
(: prf1 (Buy buying john car))
(: prf2 (Red car))

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

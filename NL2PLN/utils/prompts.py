
def make_explicit(sentence: str, similar_lst: list[str]) -> str:
    similar = '\n'.join(similar_lst)
    return f"""
You are tasked with making all implicit information in a sentence explicit. Here is the sentence:

<sentence>
{sentence}
</sentence>

Your goal is to rewrite this sentence, making all implicit information explicit. Follow these guidelines:

1. Identify any implied subjects, objects, or actions that are not directly stated.
2. Add the implied thigns to the sentence.
3. Try to keep the sentence as concise as possible.
4. Change as little as possible while still making the meaning of the sentence explicit.

Provide your final output enclosed within triple backticks (```). The output should be a single, coherent sentence.

Here are some examples of previous conversions for reference:
{similar}

Now, please rewrite the given sentence, making all implicit information explicit.
"""

def nl2pl(sentence: str, similar_lst: list[str]) -> str:
    similar = '\n'.join(similar_lst)
    return f"""
You are tasked with converting a sentence to first-order predicate logic. Here is the sentence:

<sentence>
{sentence}
</sentence>

Your goal is to convert this sentence into first-order predicate logic notation. Follow these guidelines:

1. Use simple English names for predicates.
2. Use $x, $y, $z, etc. as variable names. Use only alphanumeric characters after the $ sign.
3. Create granular predicates. For example, instead of BigHouse($x), use (House($x) ∧ Big($x)).
4. Quantifiers should only encompase the part of the statment that is using that variable.
5. Think carefully about the logical structure of the sentence before providing your output.
6. Nested Predicates are not allowed.

Before you give your final answer, take a moment to consider the best way to represent the logical structure of the sentence. You may use <thinking> tags to show your thought process, but this is optional.

Provide your final output enclosed within triple backticks (```). The output should be comprehensible without any of the surrounding text.

Remember to use granular predicates to break down complex concepts into simpler logical components.

Here's an example to guide you:

Input: "For all students, there exists a course such that if the student is enrolled in the course and the course is difficult, then the student studies hard or seeks help."

Output:
```∀ $x (∃ $y (Student(x) ∧ Course(y) ∧ EnrolledIn(x,y) ∧ Difficult(y))) → ∃ $z ∃ $s ((Studies(z) ∧ Hard(z)  ∧  Does(x,z)) ∨ (Help(s)  ∧ Seeks(x,s)))```

Additionally, here are some examples of previous conversions, please stay consistent with the format and resuse predicates where possible:
Sentence: A Person plays the instrument quickly
Predicate Logic: ∃ $x ∃ $y ∃ $z (Person($x) ∧ Instrument($y) ∧ Play($x,$y,$z) ∧ Quick($z))
Sentence: A band entails People that play music
Predicate Logic: (∃ $x Band($x)) -> (∃ $y ∃ $z (Person($y) ∧ Play($y,$z) ∧ Music($z)))
{similar}


Now, please convert the given sentence to first-order predicate logic following these instructions.
"""
     
def fix_predicatelogic(line: str, original_pred_logic: str, error_message: str, similar: list[str]) -> str:
    similar = '\n'.join(similar)
    prompt = (
        "Fix the following predicate logic error that happened when converting the Sentence:\n"
        f"{line}\n"
        "Logic:\n"
        f"{original_pred_logic}\n"
        "Error:\n"
        f"{error_message}\n"
        "Similar Sentences (for reference):\n"
        f"{similar}\n"
        "Output the fixed logic in between triple backticks."
    )
    return prompt

def pln2nl(pln: str, similar_examples: list[str]) -> str:
    similar = '\n'.join(similar_examples)
    return f"""
You are an AI assistant specialized in translating OpenCog PLN (Probabilistic Logic Networks) statements into natural language. Your task is to convert the following PLN statement into clear, concise English:

<pln>
{pln}
</pln>

Please provide a natural language explanation of what this PLN statement means. Make sure your explanation is easy to understand for someone who isn't familiar with PLN syntax. Focus on conveying the meaning and implications of the statement.

Provide your final output enclosed within triple backticks (```). It should be a single sentence that is comprehensible without any of the surrounding text.

Here's an example to guide you:

Input PLN:
(InheritanceLink
    (ConceptNode "Dog")
    (ConceptNode "Mammal")
)

Output:
This statement indicates that all dogs belong to the broader category of mammals, sharing characteristics common to all mammals.
```Dogs are mammals```

Additionally, here are some examples of previous conversions for reference:
{similar}

Now, please provide a natural language explanation for the given PLN statement:
"""

def nl2pln_old(sentence: str, similar: list[str]) -> str:
    similar = '\n'.join(similar)
    return f"""
You are tasked with converting a sentence to OpenCog PLN (Probabilistic Logic Networks) format, including necessary preconditions. Here is the sentence:

<sentence>
{sentence}
</sentence>

Your goal is to convert this sentence into OpenCog PLN notation and identify any necessary preconditions. Follow these guidelines:

1. Use simple English names for concepts and relationships.
2. Use the appropriate OpenCog PLN syntax, including InheritanceLink, EvaluationLink, and ConceptNode.
3. Break down complex concepts into simpler components using multiple links when necessary.
4. Consider what must be true for this sentence to make sense, and include these as preconditions.
5. Use VariableNodes when appropriate, naming them $X, $Y, $Z, etc.
6. Don't include a TruthValue

Provide your output enclosed within triple backticks (```). The output should have two sections:
- Preconditions: List any PLN statements that must be true for the main statement to make sense
- Statement: The main PLN representation of the sentence

Here's an example:

Input: "The dog chased the cat in the garden"

Output:
```
Preconditions:
(ExistsLink 
    (ConceptNode "Dog")
)
(ExistsLink 
    (ConceptNode "Cat")
)
(ExistsLink 
    (ConceptNode "Garden")
)

Statement:
(EvaluationLink
    (PredicateNode "chase_in")
    (ListLink
        (ConceptNode "Dog")
        (ConceptNode "Cat")
        (ConceptNode "Garden")
    )
)
```

Additionally, here are some examples of previous conversions for reference:
{similar}

Now, please convert the given sentence to OpenCog PLN format following these instructions.
"""


def nl2pln(sentence: str, similar_lst: list[str], previous_lst: list[str]) -> str:
    similar = '\n'.join(similar_lst)
    previous = '\n'.join(previous_lst)
    return f"""
You are an expert in natural language understanding and dependent type theory. Your task is to convert English sentences into formal logic using dependent types.

For any given English sentence, you should:

1. Identify the key entities (nouns, proper names)
2. Identify properties/traits (adjectives)
3. Identify relationships (verbs, prepositions)
4. Express these in dependent type theory notation
5. Resolve any references to previously mentioned entities

Guidelines for the conversion:
- Create Type declarations for all entities
- Use the following type operators:
  * -> for functions and dependent products (Π types)
  * Σ for dependent sums (existential types) - use for existential quantification
  * | for sum types (disjoint unions)
  * * for product types (pairs/tuples)
  * ∩ for intersection types
  * ∪ for union types
- For questions use a Variable $var (always start with a $)
  * Where is X => (Location X $loc)
  * How is X relateed to Y => ($rel X Y)
- For quantifiers:
  * Universal ("all", "every"): Use dependent product (->)
  * Existential ("some", "a"): If then number of objects is clear just define them all explicitly
                               If not, use dependent sum (Σ)
- For anaphora resolution:
  * Check previous sentences for referenced entities
  * Reuse entity identifiers from previous context
  * Link pronouns to most recently mentioned matching entity
- Include all necessary preconditions
- Express the final statement using proof terms
- Keep it simple and convert only explicit information

There is only one Base type namely (: Object Type). Everything else is an n-ary predicate.
i.e. (: Human (-> Object Type))

Your output must follow this format:
From Context:
[Declarations and expressions that already exist in the context]

Type Definitions:
[Type declarations for predicates and relationships]

Statements:
[Entity declarations and logical expressions]

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

6. Intersection Types (∩):
"John is both a student and an athlete"
```
Type Definitions:
(: Student (-> Object Type))
(: Athlete (-> Object Type))

Statements:
(: john Object)
(: prf1 (∩ (Student john) (Athlete john)))
```

7. Union Types (∪):
"The audience consists of adults and children"
```
Type Definitions:
(: Audience (-> Object Type))
(: Adult (-> Object Type))
(: Child (-> Object Type))

Statements:
(: audience Object)
(: prf1 (-> (Audience x) (∪ (Adult x) (Child x))))
```

For performatives and other expressions without logical meaning just output:
```
Performative
```

In the context we always have the following objects:
(: authorSpeaker Object)
(: readerLister Object)
(: placeTime Object)

Here is a list of similar sentences that have already been translated and placed into the context:
{similar}

If the following sentence talks about objects already mentioned in the context don't create duplicates.

And here are the sentences that have come before so you can resolve anaphora:
{previous}

Now, convert the following English sentence into formal logic using dependent types:
{sentence}

"""

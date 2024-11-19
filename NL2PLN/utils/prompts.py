
def make_explicit(sentence, similar):
    similar = '\n'.join(similar)
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

def nl2pl(sentence, similar):
    similar = '\n'.join(similar)
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
     
def fix_predicatelogic(line, original_pred_logic, error_message, similar):
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

def pln2nl(pln, similar_examples):
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

def nl2pln_old(sentence, similar):
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


def nl2pln(sentence, similar):
    similar = '\n'.join(similar)
    return f"""
You are an expert in natural language understanding and dependent type theory. Your task is to convert English sentences into formal logic using dependent types.

For any given English sentence, you should:

1. Identify the key entities (nouns, proper names)
2. Identify properties/traits (adjectives)
3. Identify relationships (verbs, prepositions)
4. Express these in dependent type theory notation

Guidelines for the conversion:
- Create Type declarations for all entities
- Use the following type operators:
  * -> for functions and dependent products (Π types)
  * Σ for dependent sums (existential types)
  * | for sum types (disjoint unions)
  * * for product types (pairs/tuples)
  * ∩ for intersection types
  * ∪ for union types
- Include all necessary preconditions
- Express the final statement using proof terms
- Keep it simple
- The results should be surounded by ``` and ```

There is only one Base type namly (: Object Type) everythign else is a n-ary predicate.
i.e. (: Human (-> Object Type))

Your output must follow this format:
Type Definitions:
[Type declarations for predicates and relationships]

Statements:
[Entity declarations and logical expressions]

Example:

Input:
"Max, a curious GoldenRetriver, spotted a Butterfly in the garden."

Output:
...Thoughts...
```
Type Definitions:
(: GoldenRetriver (-> Object Type))
(: Butterfly (-> Object Type))
(: Curious (-> Object Type))
(: Spotted (-> Object Object Type))

Statements:
(: max Object)
(: maxGoldenRetriver (GoldenRetriver max))
(: maxCurious (Curious max))
(: bf Object)
(: bfButterfly (Butterfly bf))
(: prf1 (Spotted max bf))
```

For performatives ant other expressions without logical mean just output:
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

Now, convert the following English sentence into formal logic using dependent types:
{sentence}

"""


def nl2pl(sentence,similar):
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

Provide your final output enclosed within triple backticks (```). The output should be comprehensible without any surrounding text.

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

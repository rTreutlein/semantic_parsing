# Consistency Issues in PLN Translations

## Spelling Fixes Needed
- "RecivesHelp" should be "ReceivesHelp" in homework helping statements

## Temporal Relationship Patterns
- Currently mixing unary predicates (Sometimes/Always/Recently) with binary relations (AtTime/When)
- Consider standardizing approach for temporal expressions
- Document when to use each if both patterns are kept

## Activity Patterns
- Good pattern: ProvidesHelp/ReceivesHelp shows both sides of interaction
- Consider applying similar bidirectional pattern to other multi-participant activities
- Example: PlayTogether could be more explicit about participants' roles

## Location Relationships
- Multiple predicates: In/LiveIn/LiveOn
- Need clear rules for when to use each
- Consider if all are necessary or if some could be combined

## Mental/Emotional State Patterns
- Inconsistent representation between unary predicates and relations
- Examples:
  - (Happy feeling) as unary predicate
  - (Feels feelrel authorSpeaker feeling) as relation
  - (Love loving authorSpeaker english) as relation
- Consider standardizing on one approach

## Quantity Representations
- Explicit counting: (NumberOfSharers sharing 4)
- Implicit counting: creating separate objects/statements
- Need consistent approach for representing quantities
- Consider when to use explicit count vs. separate statements

## Query Patterns
- Inconsistent use of existential variables
- Variable naming conventions vary ($prf vs other names)
- Some queries use complex patterns with (*...), others direct
- Need standardized approach for question representation

## To Be Investigated
- Continue analyzing for more consistency issues
- Review handling of possessives
- Check consistency of verb tense representations
- Analyze patterns in compound statements

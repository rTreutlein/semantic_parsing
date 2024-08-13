# Corpus Bootstrapping Process

## Overview

This document outlines the process of bootstrapping our corpus using everyday examples and common sense reasoning. The goal is to create a self-consistent and expandable knowledge base using Large Language Models (LLMs), focusing on simple, shorter sentences that capture everyday knowledge.

## Seed Rules

We start with a small set of seed rules that serve as the foundation for our corpus. These rules should be:

1. Simple and related to everyday life
2. Capturing common sense knowledge or logical relationships
3. Expressed as clear, factual statements that can be translated into predicate logic

Example seed rule:
- "If a plant receives sunlight, it grows."

## Bootstrapping Steps

1. **Seed Rule Expansion**
   - For each seed rule, use the LLM to generate 1-3 related rules for each relationship type.
   - Keep rules simple and focused on logical relationships that can be translated into predicate logic.

2. **Knowledge Graph Creation**
   - Create a knowledge graph where each node is a rule from the corpus.
   - Edges represent relationships between rules.
   - Use the following edge types:
     a. Specializes: Provides a more specific version of the rule
     b. Generalizes: Presents a more general version of the rule
     c. Complements: Adds complementary information to the rule
     d. Negates: Presents an opposing or contradictory rule
     e. Rephrase: Restates the rule using different words while maintaining the same meaning

3. **Iterative Expansion**
   - Select rules from the knowledge graph for further expansion.
   - For each selected rule, generate new rules using the expand_rule method.
   - Add new rules to the knowledge graph with appropriate relationships.

4. **Consistency Check**
   - Ensure that generated rules maintain logical consistency within the knowledge graph.
   - Resolve any contradictions or ambiguities.

5. **Validation**
   - Periodically validate the entire corpus for internal consistency.
   - Verify that rules can be translated into predicate logic.
   - Check that edge relationships are correctly applied and meaningful.

## LLM Prompting Strategies

- Use clear, specific prompts that encourage simple, factual rules.
- Include instructions for maintaining consistency with existing rules.
- Encourage the generation of rules that can be easily translated into predicate logic.
- For each relationship type:
  a. Provide clear examples of how to generate rules with that relationship.
  b. Ask the LLM to consider different aspects or implications of the input rule.
  c. Encourage the LLM to generate rules that maintain logical consistency within the knowledge graph.

## Quality Control

- Prioritize clarity and simplicity in generated content.
- Regularly review and curate the corpus to maintain high quality and relevance to everyday life.
- Consider human review for ensuring common sense accuracy.

## Expansion and Refinement

As the corpus grows:
- Identify common themes or domains in everyday life for focused expansion.
- Develop more nuanced relationships between sentences.
- Maintain a balance between different areas of common knowledge.

By following this process, we aim to create a robust, self-consistent, and expandable corpus that captures everyday knowledge and common sense reasoning.

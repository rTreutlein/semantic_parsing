# Corpus Bootstrapping Process

## Overview

This document outlines the process of bootstrapping our corpus using everyday examples and common sense reasoning. The goal is to create a self-consistent and expandable knowledge base using Large Language Models (LLMs), focusing on simple, shorter sentences that capture everyday knowledge.

## Seed Sentences

We start with a small set of seed sentences that serve as the foundation for our corpus. These sentences should be:

1. Simple and related to everyday life
2. Capturing common sense knowledge
3. Diverse in structure to allow for natural language variation

Example seed sentences:
- "Apples grow on trees."
- "Water boils at 100 degrees Celsius."
- "Dogs bark to communicate."

## Bootstrapping Steps

1. **Seed Sentence Expansion**
   - For each seed sentence, use the LLM to generate 2-3 related facts or rephrased versions.
   - Keep sentences short and simple, focusing on everyday knowledge.

2. **Cross-Referencing**
   - Use the LLM to identify potential connections between different sentences.
   - Generate new sentences that bridge related concepts.

3. **Consistency Check**
   - Run all generated content through the LLM to check for logical consistency.
   - Resolve any contradictions or ambiguities.

4. **Knowledge Graph Creation**
   - Create a simple knowledge graph where each node is a sentence from the corpus.
   - Edges represent relationships or connections between sentences.
   - Use the following edge types:
     a. Rephrases: Restates the sentence in a different way
     b. Explains: Provides further explanation for a part of the sentence
     c. Implies: Presents a more general scenario implied by the sentence
     d. Contrasts: Shows a difference or opposite
     e. Compares: Highlights similarities with another concept

5. **Iterative Expansion**
   - Select sentences from the knowledge graph for further expansion or rephrasing.
   - For each selected sentence, generate 1-2 new sentences for each applicable edge type.
   - Repeat steps 1-4 for these new focus areas.

6. **Validation**
   - Periodically validate the entire corpus for internal consistency.
   - Use common sense reasoning to verify the accuracy of statements.
   - Check that edge relationships are correctly applied and meaningful.

## LLM Prompting Strategies

- Use clear, specific prompts that encourage simple, factual responses.
- Include instructions for maintaining consistency with existing information.
- Encourage variation in sentence structure and phrasing.
- For cross-referencing (step 2):
  a. Use prompts that ask the LLM to identify concepts or keywords in the existing sentences.
  b. Ask the LLM to find connections between these concepts and other common knowledge areas.
  c. Request bridging sentences that link the identified concepts to new, related ideas.
  d. Encourage the LLM to consider different perspectives or contexts for the existing information.

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

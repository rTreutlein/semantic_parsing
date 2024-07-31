# Bootstrapping Example: Step-by-Step Process

This document demonstrates the corpus bootstrapping process using the example seed sentence: "Coffee wakes people up."

## 1. Seed Sentence Expansion

Using an LLM, we generate 2-3 related facts or rephrased versions:

1. "Caffeine in coffee helps people feel more alert."
2. "Many people drink coffee in the morning to start their day."
3. "Coffee is a popular beverage known for its energizing effects."

## 2. Cross-Referencing

We use the LLM to identify connections with other concepts and generate bridging sentences:

1. "Tea, like coffee, contains caffeine and can also increase alertness."
2. "Some people prefer decaf coffee to avoid caffeine's effects on sleep."

## 3. Consistency Check

We run all generated content through the LLM to check for logical consistency. In this case, all statements appear to be consistent with each other and with common knowledge.

## 4. Knowledge Graph Creation

We create a simple knowledge graph where each node is a sentence from our corpus:

- Node: "Coffee wakes people up."
  - Edge (elaborates) -> Node: "Caffeine in coffee helps people feel more alert."
  - Edge (elaborates) -> Node: "Many people drink coffee in the morning to start their day."
  - Edge (rephrases) -> Node: "Coffee is a popular beverage known for its energizing effects."
- Node: "Tea, like coffee, contains caffeine and can also increase alertness."
  - Edge (compares) -> Node: "Coffee wakes people up."
- Node: "Some people prefer decaf coffee to avoid caffeine's effects on sleep."
  - Edge (contrasts) -> Node: "Caffeine in coffee helps people feel more alert."

## 5. Iterative Expansion

We select sentences from the knowledge graph for further expansion. For example, we might choose to expand on "Many people drink coffee in the morning to start their day":

1. "Breakfast often includes a cup of coffee for many adults."
2. "Some coffee shops experience rush hours during early morning commutes."

## 6. Validation

We periodically validate the entire corpus for internal consistency and use common sense reasoning to verify the accuracy of statements. In this case, we might ask a few people about their coffee habits to confirm the general accuracy of our statements.

This example demonstrates how a single seed sentence about an everyday topic can be expanded into a network of related, common-sense statements, forming the basis of a self-consistent and expandable corpus.

## 7. Additional Edge Type Examples

Using "Coffee wakes people up" as the original sentence, here are examples for each edge type:

1. Elaborates:
   - Original: "Coffee wakes people up."
   - Elaboration: "Coffee contains caffeine, a stimulant that increases alertness and reduces fatigue."

2. Specifies:
   - Original: "Coffee wakes people up."
   - Specification: "A strong espresso shot can quickly boost energy levels in the morning."

3. Generalizes:
   - Original: "Coffee wakes people up."
   - Generalization: "Caffeinated beverages often have stimulating effects on the human body."

4. Contrasts:
   - Original: "Coffee wakes people up."
   - Contrast: "Chamomile tea is known for its calming properties and is often consumed before bedtime."

5. Compares:
   - Original: "Coffee wakes people up."
   - Comparison: "Like coffee, energy drinks also contain caffeine and are used to increase alertness."

6. Causes:
   - Original: "Coffee wakes people up."
   - Cause: "The caffeine in coffee blocks adenosine receptors in the brain, causing increased alertness."

7. Results_from:
   - Original: "Coffee wakes people up."
   - Result: "Many people experience improved concentration and productivity as a result of drinking coffee."

8. Exemplifies:
   - Original: "Coffee wakes people up."
   - Example: "A college student drinking a large coffee before an early morning exam exemplifies how people use coffee to stay alert."

9. Defines:
   - Original: "Coffee wakes people up."
   - Definition: "Coffee is a brewed beverage prepared from roasted coffee beans, known for its stimulating effects due to its caffeine content."

These examples show how each edge type can be used to create a rich network of related information around the original sentence, expanding the corpus with diverse yet connected knowledge.

# Bootstrapping Example: Step-by-Step Process

This document demonstrates the corpus bootstrapping process using the example seed sentence: "The Earth orbits the Sun."

## 1. Seed Sentence Expansion

Using an LLM, we generate 3-5 related facts or explanations:

1. "The Earth's orbit around the Sun is elliptical, not perfectly circular."
2. "It takes approximately 365.25 days for the Earth to complete one orbit around the Sun."
3. "The Earth's orbital path is called its 'ecliptic.'"
4. "The Earth's distance from the Sun varies throughout its orbit, ranging from about 147 to 152 million kilometers."

## 2. Cross-Referencing

We use the LLM to identify connections with other concepts and generate bridging sentences:

1. "The Earth's orbital motion, along with its axial tilt, causes the seasons we experience on our planet."
2. "Other planets in our solar system also orbit the Sun, each with its own unique orbital characteristics."
3. "The study of celestial bodies' movements, including Earth's orbit, falls under the field of celestial mechanics."

## 3. Consistency Check

We run all generated content through the LLM to check for logical consistency. In this case, all statements appear to be consistent with each other and with widely accepted scientific knowledge.

## 4. Knowledge Graph Creation

We create a simple knowledge graph representing the relationships between concepts:

- Node: Earth
  - Edge (orbits) -> Node: Sun
  - Edge (has property) -> Node: Elliptical orbit
  - Edge (has property) -> Node: Orbital period (365.25 days)
  - Edge (has property) -> Node: Ecliptic
  - Edge (varies in distance from) -> Node: Sun (147-152 million km)
- Node: Earth's orbit
  - Edge (causes) -> Node: Seasons (along with axial tilt)
- Node: Solar System
  - Edge (contains) -> Node: Earth
  - Edge (contains) -> Node: Other planets
- Node: Celestial mechanics
  - Edge (studies) -> Node: Earth's orbit

## 5. Iterative Expansion

We select nodes from the knowledge graph for further expansion. For example, we might choose to expand on "Seasons":

1. "Earth's axial tilt of approximately 23.5 degrees is the primary cause of seasons."
2. "When the Northern Hemisphere is tilted towards the Sun, it experiences summer, while the Southern Hemisphere experiences winter."
3. "The solstices mark the points in Earth's orbit where one hemisphere is most tilted towards or away from the Sun."

## 6. Validation

We periodically validate the entire corpus for internal consistency and use external sources to fact-check key statements. In this case, we might consult astronomy textbooks or NASA's website to verify the information about Earth's orbit and seasons.

This example demonstrates how a single seed sentence can be expanded into a network of related concepts, forming the basis of a self-consistent and expandable corpus.

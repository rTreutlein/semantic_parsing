"""
This file describes the steps to integrate the corpusgenerator into the convert_to_predicate_logic.py pipeline.
"""

import os
from corpusgenerator.utils.utils import print_deepest_path
from corpusgenerator.generator import generate_corpus
from convert_to_predicate_logic import process_sentence, metta_handler
from utils.ragclass import RAG

def integrate_corpusgenerator():
    """
    Steps to integrate corpusgenerator into the convert_to_predicate_logic.py pipeline:
    """

    # Step 1: Generate the initial corpus
    graph, roots = generate_corpus()

    # Step 2: Print the deepest path in the generated corpus
    print_deepest_path(graph, roots)

    # Step 3: Initialize RAG instances for explicit sentences and predicate logic
    rag_explicit = RAG(collection_name="generated_corpus_explicit")
    rag_predicate = RAG(collection_name="generated_corpus_predicate")

    # Step 4: Process each sentence in the graph
    for node in graph.nodes():
        sentence = graph.nodes[node]['text']
        
        # Step 5: Convert the sentence to predicate logic
        metta_atom = process_sentence(sentence, rag_explicit, rag_predicate, node)
        
        if metta_atom:
            # Step 6: Add the MeTTa atom to the knowledge base
            metta_handler.metta.run(metta_atom)

    # Step 7: Use the updated knowledge base for further generations
    def get_similar_sentences(sentence):
        # Implement logic to retrieve similar sentences from the MeTTa knowledge base
        # This could involve querying the knowledge base or using the RAG instances
        pass

    # Step 8: Generate new sentences using the updated knowledge base
    new_graph, new_roots = generate_corpus(get_similar_sentences)

    # Step 9: Process the new sentences
    for node in new_graph.nodes():
        sentence = new_graph.nodes[node]['text']
        metta_atom = process_sentence(sentence, rag_explicit, rag_predicate, node)
        
        if metta_atom:
            metta_handler.metta.run(metta_atom)

    # Step 10: Save the final MeTTa knowledge base
    metta_handler.metta.run('!(save-space &kb "final_knowledge_base.metta")')

if __name__ == "__main__":
    integrate_corpusgenerator()

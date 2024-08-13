"""
This file describes the steps to integrate the corpusgenerator into the convert_to_predicate_logic.py pipeline.
"""

import os
from corpusgenerator.corpus_generator import CorpusGenerator
from convert_to_predicate_logic import process_sentence, metta_handler
from utils.ragclass import RAG
from utils.llm_client import OpenAIClient
from check_compound_predicates import check_and_generate_equivalences

def integrate_corpusgenerator():
    """
    Steps to integrate corpusgenerator into the convert_to_predicate_logic.py pipeline:
    """

    # Step 1: Initialize the CorpusGenerator and other necessary components
    llm_client = OpenAIClient(api_key=os.getenv("OPENAI_API_KEY"))
    corpus_generator = CorpusGenerator(llm_client)
    rag_explicit = RAG(collection_name="generated_corpus_explicit")
    rag_predicate = RAG(collection_name="generated_corpus_predicate")

    # Step 2: Start with a seed sentence
    seed_sentence = "All humans are mortal."

    # Step 3: Convert the seed sentence to predicate logic
    metta_atom = process_sentence(seed_sentence, rag_explicit, rag_predicate, "seed")
    if metta_atom:
        metta_handler.metta.run(metta_atom)

    # Step 4: Main loop for generating and processing new sentences
    for i in range(10):  # Adjust the number of iterations as needed
        # Step 5: Get a new seed sentence from the MeTTa knowledge space
        new_seed = metta_handler.metta.run('!(get-random-atom &kb)')
        
        # Step 6: Generate a new sentence using the CorpusGenerator
        new_sentences = corpus_generator.expand_rule(new_seed)
        
        # Step 7: Process the new sentence
        for new_sentence, _ in new_sentences:
            metta_atom = process_sentence(new_sentence, rag_explicit, rag_predicate, f"generated_{i}")
            if metta_atom:
                metta_handler.metta.run(metta_atom)
                
                # Check for compound predicates and generate equivalences
                equivalences = check_and_generate_equivalences(metta_atom)
                for compound, equivalence in equivalences:
                    print(f"Compound Predicate found: {compound}")
                    print(f"Generated Equivalence: {equivalence}")
                    # You can choose to add these equivalences to the MeTTa knowledge base if needed
                    # metta_handler.metta.run(f'(= ({compound} $x) {equivalence})')

    # Step 8: Save the final MeTTa knowledge base
    metta_handler.metta.run('!(save-space &kb "final_knowledge_base.metta")')

if __name__ == "__main__":
    integrate_corpusgenerator()

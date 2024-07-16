import json
import numpy as np
from pynndescent import NNDescent
from cluster.embedder import embed_from_cache
from processing.rate_complexity import analyze_sentence, calculate_complexity_score, calculate_corpus_statistics, normalize_measures
from convert_to_predicate_logic import process_file

def load_ordered_sentences(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def find_densest_cluster(embeddings, sentences, n_least_complex=10, n_neighbors=100):
    index = NNDescent(embeddings, metric="cosine", n_neighbors=n_neighbors)
    index.prepare()
    
    least_complex_indices = [sentences.index(s) for s in sentences[:n_least_complex]]
    neighbors, distances = index.query([embeddings[i] for i in least_complex_indices], k=n_neighbors)
    
    average_distances = np.mean(distances, axis=1)
    densest_cluster_index = np.argmin(average_distances)
    
    return least_complex_indices[densest_cluster_index], neighbors[densest_cluster_index]

def main(ordered_sentences_file):
    # Load ordered sentences
    ordered_sentences = load_ordered_sentences(ordered_sentences_file)
    
    # Load embeddings
    embeddings, all_sentences = embed_from_cache()
    
    # Find the densest cluster among the 10 least complex sentences
    center_index, neighbor_indices = find_densest_cluster(embeddings, all_sentences, n_least_complex=10, n_neighbors=100)
    
    # Get the sentences for the cluster
    cluster_sentences = [all_sentences[i] for i in neighbor_indices]
    
    # Calculate corpus statistics for complexity sorting
    means, std_devs, sentence_to_measures = calculate_corpus_statistics(cluster_sentences)
    
    # Define weights for complexity measures (you can adjust these as needed)
    weights = {
        'num_words': 0.5,
        'num_clauses': 0.1,
        'parse_tree_depth': 0.1,
        'num_logical_connectives': 0.1,
        'num_quantifiers': 0.1,
        'num_modifiers': 0.1,
    }
    
    # Sort cluster sentences by complexity
    sorted_cluster_sentences = sorted(
        cluster_sentences,
        key=lambda s: calculate_complexity_score(
            normalize_measures(sentence_to_measures[s], means, std_devs),
            weights
        ),
        reverse=True
    )
    
    # Save sorted cluster sentences to a file
    with open('sorted_cluster_sentences.txt', 'w', encoding='utf-8') as f:
        for sentence in sorted_cluster_sentences:
            f.write(f"{sentence}\n")
    
    # Convert sorted cluster sentences to predicate logic
    process_file('sorted_cluster_sentences.txt')

if __name__ == "__main__":
    main('path_to_your_ordered_sentences.json')

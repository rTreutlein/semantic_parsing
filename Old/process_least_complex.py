import json
import sys
from cluster.embedder import embed_sentences, embed_from_cache
from processing.sentence_complexity import calculate_complexity_score, calculate_corpus_statistics, normalize_measures, weights
from utils.ragclass import RAG
from convert_to_predicate_logic import process_sentence
from pynndescent import NNDescent
import numpy as np

def load_sentence_to_paragraph(input_file):

    """Load the sentence_to_paragraph dictionary from a JSON file."""
    with open(input_file, 'r', encoding='utf-8') as f:
        sentence_to_paragraph = json.load(f)
    print(f"Loaded sentence_to_paragraph from {input_file}")
    return sentence_to_paragraph

def load_ordered_sentences(input_file):
    """Load the ordered sentences from a JSON file."""
    with open(input_file, 'r', encoding='utf-8') as f:
        ordered_sentences = json.load(f)
    print(f"Loaded ordered sentences from {input_file}")
    return ordered_sentences

def get_densest_cluster(embeddings):
    """Get the densest cluster from the embeddings."""
    index = NNDescent(embeddings, metric="cosine", n_neighbors=10)
    index.prepare()
    neibours,distances = index.query(embeddings[-10:], k=100)
    average_distances = np.median(distances, axis=1)
    lowest_avg_distance_index = np.argmin(average_distances)
    return neibours[lowest_avg_distance_index]


if len(sys.argv) != 3:
    print("Usage: python process_least_complex.py <sentence_to_paragraph_file> <ordered_sentences_file>")
    sys.exit(1)

sentence_to_paragraph_file = sys.argv[1]
ordered_sentences_file = sys.argv[2]

sentence_to_paragraph = load_sentence_to_paragraph(sentence_to_paragraph_file)
#ordered_sentences = load_ordered_sentences(ordered_sentences_file)

#embeddings = embed_sentences(ordered_sentences)
embeddings,sentences = embed_from_cache()
print('\n'.join(sentences[-10:]))
print(embeddings.shape)
densest_cluster = get_densest_cluster(embeddings)
#densest_cluster contains the sentence index convert to sentence list
densest_cluster = [sentences[i] for i in densest_cluster]

for i in densest_cluster:
    print(i)

print("-"*100)

# Calculate corpus statistics
means, std_devs, sentence_to_measures = calculate_corpus_statistics(sentences)

#sort cluster by complexity
sorted_cluster = sorted(
        densest_cluster,
        key=lambda s: calculate_complexity_score(
            normalize_measures(sentence_to_measures[s], means, std_devs),
            weights
        ),
    )

# Process sentences
rag = RAG(collection_name="least_complex")

for sentence in sorted_cluster:
    print(sentence)
    #metta = process_sentence(sentence, rag)
    #print(metta)

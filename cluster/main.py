import json
import numpy as np
import time
from data_processor import process_jsonl
from embedder import embed_sentences, embed_from_cache
from cluster_rater import cluster_and_rate

from pynndescent import NNDescent

def main1():
    # Process JSONL file
    entailment_pairs = process_jsonl('example.jsonl')
    
    # Combine sentences
    combined_sentences = [f"{pair[0]} entails {pair[1]}" for pair in entailment_pairs]
    
    # Embed sentences
    embeddings = embed_sentences(combined_sentences)

def main():
    embeddings, sentences = embed_from_cache()

    start_time = time.time()
    index = NNDescent(embeddings, metric="cosine", n_neighbors=5)
    index.prepare()
    end_time = time.time()
    
    print(f"Time taken to build index: {end_time - start_time:.2f} seconds")

    start_time = time.time()
    neibours,distances = index.query(embeddings, k=1000)
    average_distances = np.median(distances, axis=1)
    lowest_avg_distance_index = np.argmin(average_distances)

    neibours,distances = index.query([embeddings[neibours[lowest_avg_distance_index][0]]], k=10000)

    with open('output.txt', 'w') as f:
        for elem in neibours[0]:
            f.write(sentences[elem] + '\n')

    end_time = time.time()
    print(f"Time taken to query 1000 elems: {end_time - start_time:.2f} seconds")

    # Cluster and rate
    #clusters, ratings = cluster_and_rate(embeddings[:1000], sentences[:1000], 100)
    
    # Print results
    #for i, (cluster, rating) in enumerate(zip(clusters, ratings)):
        #print(f"Cluster {i + 1}:")
        #for idx in cluster:
            #print(f"  - {sentences[idx]}")
        #print(f"  Rating: {rating}")
        #print()

if __name__ == "__main__":
    main()

from scipy.cluster.hierarchy import linkage
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity

def cluster_and_rate(embeddings, sentences, min_cluster_size=2):
    # Perform hierarchical clustering
    Z = linkage(embeddings, method='average', metric='cosine')
    
    # Generate all possible clusters
    all_clusters = {}
    for i in range(len(Z)):
        cluster_id = i + len(embeddings)
        left_child = int(Z[i][0])
        right_child = int(Z[i][1])
        if left_child < len(embeddings):
            left_cluster = [left_child]
        else:
            left_cluster = all_clusters[left_child]
        if right_child < len(embeddings):
            right_cluster = [right_child]
        else:
            right_cluster = all_clusters[right_child]
        all_clusters[cluster_id] = left_cluster + right_cluster
    
    # Filter clusters based on size
    filtered_clusters = {k: v for k, v in all_clusters.items() if len(v) >= min_cluster_size}
    
    # Rate clusters
    ratings = []
    for cluster_id, indices in filtered_clusters.items():
        cluster_sentences = [sentences[i] for i in indices]
        cluster_embeddings = [embeddings[i] for i in indices]
        similarity_matrix = cosine_similarity(cluster_embeddings)
        np.fill_diagonal(similarity_matrix, 0)  # Set diagonal to 0 to exclude self-similarity
        density = np.mean(similarity_matrix)
        avg_length = np.mean([len(sentence.split()) for sentence in cluster_sentences])
        rating = density * (1 / avg_length)
        ratings.append((cluster_id, rating))
    
    # Sort clusters and ratings by rating (descending order)
    sorted_ratings = sorted(ratings, key=lambda x: x[1], reverse=True)
    sorted_clusters = [filtered_clusters[cluster_id] for cluster_id, _ in sorted_ratings]
    sorted_ratings = [rating for _, rating in sorted_ratings]
    
    return sorted_clusters, sorted_ratings

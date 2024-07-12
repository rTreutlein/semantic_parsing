import uuid
import requests
import logging
from qdrant_client import QdrantClient
from qdrant_client.http import models
from qdrant_client.http.exceptions import UnexpectedResponse
from requests.exceptions import RequestException, Timeout

# Configure logging
#logging.basicConfig(level=logging.INFO)
#logger = logging.getLogger(__name__)

OLLAMA_BASE_URL = "http://spc:11434"  # Adjust this if your Ollama server is running on a different address

qdrant_client = QdrantClient("http://localhost:6333")
    #url="https://5bc23eb9-bcdb-43d6-ac1c-fa2aaf3a72fb.us-east4-0.gcp.cloud.qdrant.io:6333", 
    #api_key="WICz1oD4zJbnqr-SNnnc_bkKS6PWy1a_OKjjTMiwB8kVUUsJYvgERQ",
    #timeout=30  # Set a 30-second timeout for Qdrant operations
#)

def get_embedding(text):
    """
    Get the embedding for a given text using Ollama's API.
    """
    try:
        response = requests.post(
            f"{OLLAMA_BASE_URL}/api/embeddings",
            json={"model": "rjmalagon/gte-qwen2-7b-instruct-embed-f16", "prompt": text},  # Adjust the model name if needed
            timeout=30  # Set a 30-second timeout for the request
        )
        response.raise_for_status()
        return response.json()['embedding']
    except Timeout:
        print("Timeout occurred while getting embedding from Ollama API")
        raise
    except RequestException as e:
        print(f"Error occurred while getting embedding: {str(e)}")
        raise

def store_embedding_in_qdrant(text):
    """
    Store the embedding of a predicate in Qdrant if it doesn't already exist.
    """
    embedding = get_embedding(text)
    qdrant_client.upsert(
        collection_name="sentences",
        points=[
            models.PointStruct(
                id=str(uuid.uuid4()),  # Use a UUID as the ID
                vector=embedding,
                payload={"text": text}
            )
        ]
    )

def ensure_predicates_collection():
    """
    Ensure the "predicates" collection exists in Qdrant.
    """
    collections = qdrant_client.get_collections().collections
    if not any(collection.name == "sentences" for collection in collections):
        qdrant_client.create_collection(
            collection_name="sentences",
            vectors_config=models.VectorParams(size=3584, distance=models.Distance.COSINE),
        )
        print("Created 'sentences' collection in Qdrant")


def search_similar_predicates(sentence, limit=3):
    #logger.info(f"Searching for similar predicates to: {sentence}")
    collection_name = "sentences"
    
    try:
        # Get the embedding for the sentence
        query_vector = get_embedding(sentence)
        
        # Search for similar predicates
        search_result = qdrant_client.search(
            collection_name=collection_name,
            query_vector=query_vector,
            limit=limit
        )
        
        # Extract predicates from the search results
        similar_predicates = [hit.payload.get("text") for hit in search_result]
        #logger.info(f"Found {len(similar_predicates)} similar predicates")
        
        return similar_predicates
    except Timeout:
        print("Timeout occurred during the search operation")
        return []
    except UnexpectedResponse as e:
        print(f"Unexpected response from Qdrant: {str(e)}")
        return []
    except Exception as e:
        print(f"An unexpected error occurred: {str(e)}")
        return []

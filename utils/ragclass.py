import uuid
import requests
from qdrant_client import QdrantClient
from qdrant_client.http import models
from qdrant_client.http.exceptions import UnexpectedResponse
from requests.exceptions import RequestException, Timeout

class RAG:
    def __init__(self, collection_name="sentences", ollama_base_url="http://127.0.0.1:11434", qdrant_url="http://truenas:9333"):
        self.collection_name = collection_name
        self.ollama_base_url = ollama_base_url
        self.qdrant_client = QdrantClient(qdrant_url)
        self.ensure_collection()

    def get_embedding(self, text):
        """
        Get the embedding for a given text using Ollama's API.
        """
        try:
            response = requests.post(
                f"{self.ollama_base_url}/api/embeddings",
                json={"model": "nomic-embed-text", "prompt": text},
                timeout=30
            )
            response.raise_for_status()
            return response.json()['embedding']
        except Timeout:
            print("Timeout occurred while getting embedding from Ollama API")
            raise
        except RequestException as e:
            print(f"Error occurred while getting embedding: {str(e)}")
            raise

    def store_embedding(self, text):
        """
        Store the embedding of a predicate in Qdrant if it doesn't already exist.
        """
        embedding = self.get_embedding(text)
        self.qdrant_client.upsert(
            collection_name=self.collection_name,
            points=[
                models.PointStruct(
                    id=str(uuid.uuid4()),
                    vector=embedding,
                    payload={"text": text}
                )
            ]
        )

    def ensure_collection(self):
        """
        Ensure the collection exists in Qdrant.
        """
        collections = self.qdrant_client.get_collections().collections
        if not any(collection.name == self.collection_name for collection in collections):
            self.qdrant_client.create_collection(
                collection_name=self.collection_name,
                vectors_config=models.VectorParams(size=3584, distance=models.Distance.COSINE),
            )
            print(f"Created '{self.collection_name}' collection in Qdrant")

    def search_similar(self, sentence, limit=3):
        try:
            query_vector = self.get_embedding(sentence)
            search_result = self.qdrant_client.search(
                collection_name=self.collection_name,
                query_vector=query_vector,
                limit=limit
            )
            similar_items = [hit.payload.get("text") for hit in search_result]
            return similar_items
        except Timeout:
            print("Timeout occurred during the search operation")
            return []
        except UnexpectedResponse as e:
            print(f"Unexpected response from Qdrant: {str(e)}")
            return []
        except Exception as e:
            print(f"An unexpected error occurred: {str(e)}")
            return []

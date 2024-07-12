from ragclass import RAG

# Initialize the RAG class with default parameters
rag = RAG()

# Existing functions now use the RAG class methods
def get_embedding(text):
    return rag.get_embedding(text)

def store_embedding_in_qdrant(text):
    rag.store_embedding(text)

def ensure_predicates_collection():
    rag.ensure_collection()

def search_similar_predicates(sentence, limit=3):
    return rag.search_similar(sentence, limit)

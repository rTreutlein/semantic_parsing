import ollama
import json
import os
import base64
import numpy as np
from tqdm import tqdm
from datetime import datetime

CACHE_DIR = 'embeddings_cache'
CACHE_FILE_PREFIX = 'embeddings_cache_'
CACHE_SAVE_FREQUENCY = 10000

def load_cache():
    cache = {}
    if os.path.exists(CACHE_DIR):
        for filename in sorted(os.listdir(CACHE_DIR)):
            if filename.startswith(CACHE_FILE_PREFIX):
                with open(os.path.join(CACHE_DIR, filename), 'r') as f:
                    file_cache = json.load(f)
                    for key, value in file_cache.items():
                        if isinstance(value, list):  # Old format
                            cache[key] = np.array(value)
                        else:  # New format (base64 encoded)
                            cache[key] = np.frombuffer(base64.b64decode(value), dtype=np.float32)
    return cache

def get_latest_cache_filename():
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"{CACHE_FILE_PREFIX}{timestamp}.json"

def save_cache(new_cache, full_cache):
    if not os.path.exists(CACHE_DIR):
        os.makedirs(CACHE_DIR)
    
    delta_cache = {k: v for k, v in new_cache.items() if k not in full_cache}
    if delta_cache:
        filename = get_latest_cache_filename()
        encoded_cache = {k: base64.b64encode(v.astype(np.float32).tobytes()).decode('utf-8') for k, v in delta_cache.items()}
        with open(os.path.join(CACHE_DIR, filename), 'w') as f:
            json.dump(encoded_cache, f)

def embed_from_cache():
    cache = load_cache()
    sentences = [key for key, value in cache.items()]
    embeddings = [value for key, value in cache.items()]
    return np.array(embeddings),sentences

def embed_sentences(sentences):
    client = ollama.Client(host='http://spc:11434')
    embeddings = []
    new_cache = {}
    cache = load_cache()
    newcnt = 0
    
    for i, sentence in enumerate(tqdm(sentences, desc="Embedding sentences", unit="sentence")):
        if sentence in cache:
            embeddings.append(cache[sentence])
        else:
            #response = client.embeddings(model='rjmalagon/gte-qwen2-7b-instruct-embed-f16', prompt=sentence)
            response = client.embeddings(model='nomic-embed-text', prompt=sentence)
            embedding = np.array(response['embedding'], dtype=np.float32)
            new_cache[sentence] = embedding
            embeddings.append(embedding)
            newcnt = newcnt + 1
        
        # Save cache periodically
        if newcnt % CACHE_SAVE_FREQUENCY == 0:
            save_cache(new_cache, cache)
            cache.update(new_cache)
            new_cache = {}
            newcnt = 0
    
    # Final save to ensure all embeddings are cached
    save_cache(new_cache, cache)
    
    return embeddings

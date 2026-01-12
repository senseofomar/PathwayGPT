import faiss
import pickle
from sentence_transformers import SentenceTransformer

INDEX_PATH = "semantic_index.faiss"
MAPPING_PATH = "semantic_mapping.pkl"

# Load model only once
SEM_MODEL = SentenceTransformer("all-MiniLM-L6-v2")

def load_semantic_index():
    """Load FAISS index + mapping from disk."""
    index = faiss.read_index(INDEX_PATH)
    with open(MAPPING_PATH, "rb") as f:
        mapping = pickle.load(f)
    return index, mapping

def semantic_search(query, index, mapping, top_k=5):
    """Perform semantic search on the FAISS index."""
    query_vec = SEM_MODEL.encode([query], convert_to_numpy=True)
    distances, indices = index.search(query_vec, top_k)
    results = []
    for idx, dist in zip(indices[0], distances[0]):
        filename, chunk = mapping[idx]
        results.append((filename, chunk, dist))
    return results

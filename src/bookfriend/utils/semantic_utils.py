import faiss
import pickle
from sentence_transformers import SentenceTransformer
import os

# Load model only once (Global cache)
SEM_MODEL = SentenceTransformer("all-MiniLM-L6-v2")

def load_semantic_index_from_path(index_path):
    """
    Loads FAISS index and mapping from a specific path.
    """
    if not os.path.exists(index_path):
        raise FileNotFoundError(f"Index not found at {index_path}")

    index = faiss.read_index(index_path)

    # Derive mapping path from index path (e.g. index_123.faiss -> index_123.pkl)
    mapping_path = index_path.replace(".faiss", ".pkl")

    if os.path.exists(mapping_path):
        with open(mapping_path, 'rb') as f:
            mapping = pickle.load(f)
    else:
        mapping = []
        print(f"⚠️ Warning: No mapping file found at {mapping_path}")

    return index, mapping


def semantic_search(query, index, mapping, top_k=5):
    """Perform semantic search on the FAISS index."""
    query_vec = SEM_MODEL.encode([query], convert_to_numpy=True)
    distances, indices = index.search(query_vec, top_k)
    results = []
    for idx, dist in zip(indices[0], distances[0]):
        if idx < len(mapping):
            entry = mapping[idx]

            # === 🛡️ FIX: Handle Dictionary Format ===
            if isinstance(entry, dict):
                filename = entry.get("file", "unknown")
                chunk = entry.get("text", "")
            else:
                # Fallback for old Tuple format (filename, chunk)
                filename, chunk = entry

            results.append((filename, chunk, dist))

    return results
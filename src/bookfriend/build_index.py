import os
import faiss
import pickle
from sentence_transformers import SentenceTransformer

CHAPTERS_FOLDER = "chapters"
INDEX_PATH = "semantic_index.faiss"
MAPPING_PATH = "semantic_mapping.pkl"

def build_index():
    model = SentenceTransformer("all-MiniLM-L6-v2")

    texts, mapping = [], []
    for fname in os.listdir(CHAPTERS_FOLDER):
        if fname.endswith(".txt"):
            with open(os.path.join(CHAPTERS_FOLDER, fname), "r", encoding="utf-8") as f:
                content = f.read()
            # Split into chunks of ~200 words
            chunks = [content[i:i+800] for i in range(0, len(content), 800)]
            for chunk in chunks:
                texts.append(chunk)
                mapping.append((fname, chunk))

    # Encode texts into embeddings
    embeddings = model.encode(texts, convert_to_numpy=True)

    # Build FAISS index
    dim = embeddings.shape[1]
    index = faiss.IndexFlatL2(dim)
    index.add(embeddings)

    # Save index + mapping
    faiss.write_index(index, INDEX_PATH)
    with open(MAPPING_PATH, "wb") as f:
        pickle.dump(mapping, f)

    print(f"✅ Built index with {len(texts)} chunks.")

if __name__ == "__main__":
    build_index()

import os
import sys
import faiss
import pickle
import re
from sentence_transformers import SentenceTransformer

# === Configuration ===
if len(sys.argv) > 2:
    CHAPTERS_DIR = sys.argv[1]   # Arg 1: Text chunks folder
    INDEX_FILE = sys.argv[2]     # Arg 2: Output FAISS file
else:
    CHAPTERS_DIR = "chapters"
    INDEX_FILE = "semantic_index.faiss"

print(f"🔍 Building Index from: {CHAPTERS_DIR}")
print(f"💾 Saving to: {INDEX_FILE}")

# Derived mapping path (index.faiss -> index.pkl)
MAPPING_FILE = INDEX_FILE.replace(".faiss", ".pkl")

# Chunking config
CHUNK_SIZE = 800               # max characters per chunk
SENTENCE_OVERLAP = 2           # overlap in sentences


def smart_chunking(text, chunk_size=800, overlap_sentences=2):
    """
    Sentence-safe chunking with bounded size and semantic overlap.
    """
    sentences = re.split(r'(?<=[.!?])\s+', text)
    chunks = []
    current = []

    def current_len():
        return sum(len(s) for s in current)

    for sentence in sentences:
        sentence = sentence.strip()
        if not sentence:
            continue

        # If adding this sentence exceeds chunk size
        if current_len() + len(sentence) > chunk_size:
            chunks.append(" ".join(current))

            # Start new chunk with sentence overlap
            overlap = current[-overlap_sentences:] if overlap_sentences > 0 else []
            current = overlap[:]

            # Ensure overlap itself doesn't exceed chunk size
            while current_len() + len(sentence) > chunk_size and len(current) > 0:
                current.pop(0)

            current.append(sentence)
        else:
            current.append(sentence)

    if current:
        chunks.append(" ".join(current))

    return chunks


def build_index():
    if not os.path.exists(CHAPTERS_DIR):
        print(f"❌ Error: '{CHAPTERS_DIR}' folder not found.")
        return

    print("⏳ Loading embedding model...")
    model = SentenceTransformer("all-MiniLM-L6-v2")

    texts = []
    mapping = []

    files = sorted(os.listdir(CHAPTERS_DIR))
    print(f"📂 Found {len(files)} files. Processing...")

    for fname in files:
        if not fname.endswith(".txt"):
            continue

        path = os.path.join(CHAPTERS_DIR, fname)
        with open(path, "r", encoding="utf-8") as f:
            content = f.read()

        if not content.strip():
            continue

        file_chunks = smart_chunking(
            content,
            chunk_size=CHUNK_SIZE,
            overlap_sentences=SENTENCE_OVERLAP
        )

        for chunk in file_chunks:
            texts.append(chunk)
            mapping.append({
                "file": fname,
                "chunk_id": len(mapping),
                "text": chunk
            })

    if not texts:
        print("❌ No text found to index.")
        return

    print(f"🔢 Encoding {len(texts)} chunks...")
    embeddings = model.encode(
        texts,
        convert_to_numpy=True,
        normalize_embeddings=True,
        show_progress_bar=True
    )

    dimension = embeddings.shape[1]

    # Cosine similarity via Inner Product
    index = faiss.IndexFlatIP(dimension)
    index.add(embeddings)

    # Save index + metadata
    faiss.write_index(index, INDEX_FILE)
    with open(MAPPING_FILE, "wb") as f:
        pickle.dump(mapping, f)

    print(f"✅ Index built successfully!")
    print(f"   → FAISS index: {INDEX_FILE}")
    print(f"   → Metadata:   {MAPPING_FILE}")


if __name__ == "__main__":
    build_index()

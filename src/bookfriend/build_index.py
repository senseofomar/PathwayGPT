import os
import faiss
import pickle
import re
from sentence_transformers import SentenceTransformer

# === CONFIGURATION ===
CHAPTERS_FOLDER = "chapters"
INDEX_PATH = "semantic_index.faiss"
MAPPING_PATH = "semantic_mapping.pkl"
CHUNK_SIZE = 800  # Target characters per chunk
OVERLAP = 100  # Overlap ensures context isn't lost at boundaries


def smart_chunking(text, chunk_size=800, overlap=100):
    """
    Splits text into chunks while respecting sentence boundaries.
    1. Splits by sentences (simple regex).
    2. Groups sentences until the chunk reaches ~800 chars.
    3. Adds a bit of overlap from the previous chunk to maintain context.
    """
    # Split text into sentences (look for [.!?] followed by space or newline)
    sentences = re.split(r'(?<=[.!?])\s+', text)

    chunks = []
    current_chunk = []
    current_len = 0

    for sentence in sentences:
        # If adding this sentence exceeds the limit, save the current chunk
        if current_len + len(sentence) > chunk_size and current_chunk:
            # Join the sentences to form the chunk text
            chunk_text = " ".join(current_chunk)
            chunks.append(chunk_text)

            # Start new chunk with some overlap (last 1-2 sentences from previous)
            # This helps the AI understand context across cut points.
            overlap_text = current_chunk[-1] if len(current_chunk) > 0 else ""
            current_chunk = [overlap_text, sentence] if len(overlap_text) < chunk_size else [sentence]
            current_len = len(" ".join(current_chunk))
        else:
            # Just add sentence to current chunk
            current_chunk.append(sentence)
            current_len += len(sentence)

    # Add the last leftover chunk
    if current_chunk:
        chunks.append(" ".join(current_chunk))

    return chunks


def build_index():
    if not os.path.exists(CHAPTERS_FOLDER):
        print(f"❌ Error: '{CHAPTERS_FOLDER}' folder not found. Did you run ingest.py?")
        return

    print("⏳ Loading embedding model... (This may take a moment)")
    # We use 'all-MiniLM-L6-v2' -> Fast, small, good enough for V1.
    model = SentenceTransformer("all-MiniLM-L6-v2")

    texts = []  # The actual text content
    mapping = []  # Metadata: (filename, text_content) - so we can cite the source later

    files = sorted(os.listdir(CHAPTERS_FOLDER))
    print(f"📂 Found {len(files)} chapters. Processing...")

    for fname in files:
        if not fname.endswith(".txt"):
            continue

        path = os.path.join(CHAPTERS_FOLDER, fname)
        with open(path, "r", encoding="utf-8") as f:
            content = f.read()

        # SKIP EMPTY FILES (Safety check)
        if not content.strip():
            continue

        # Create chunks
        file_chunks = smart_chunking(content, CHUNK_SIZE, OVERLAP)

        for chunk in file_chunks:
            texts.append(chunk)
            mapping.append((fname, chunk))  # Store where this chunk came from

    if not texts:
        print("❌ No text found to index!")
        return

    print(f"🔢 Encoding {len(texts)} chunks into vectors...")
    embeddings = model.encode(texts, convert_to_numpy=True, show_progress_bar=True)

    # Build FAISS index
    dimension = embeddings.shape[1]  # 384 for all-MiniLM-L6-v2
    index = faiss.IndexFlatL2(dimension)
    index.add(embeddings)

    # Save to disk
    faiss.write_index(index, INDEX_PATH)
    with open(MAPPING_PATH, "wb") as f:
        pickle.dump(mapping, f)

    print(f"✅ Index built! Saved to '{INDEX_PATH}'.")
    print(f"📊 Total Chunks: {len(texts)}")


if __name__ == "__main__":
    build_index()
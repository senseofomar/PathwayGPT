import os
import shutil
import sys
import subprocess
from fastapi import FastAPI, HTTPException, UploadFile, File
from pydantic import BaseModel
from typing import List
from dotenv import load_dotenv

# Load secrets
load_dotenv()

# Import core logic
from utils.semantic_utils import load_semantic_index, semantic_search
from utils.answer_generator import generate_answer
import database  # <--- NEW: Import our DB module

# === Setup App ===
app = FastAPI(
    title="BookFriend API",
    version="2.1 (DB-Integrated)",
    description="Stateful RAG API with SQLite memory."
)


# === Global State (Index Cache) ===
class AppState:
    semantic_index = None
    semantic_mapping = None


state = AppState()


@app.on_event("startup")
def startup_event():
    print("⏳ API Startup: Loading Index & DB...")
    database.init_db()  # Ensure tables exist
    reload_index()


def reload_index():
    try:
        idx, mapping = load_semantic_index()
        state.semantic_index = idx
        state.semantic_mapping = mapping
        print("✅ Index loaded successfully.")
    except Exception as e:
        print(f"⚠️ Index not found: {e}")


# === API Models ===

class IngestResponse(BaseModel):
    message: str
    book_id: str
    title: str


class QueryRequest(BaseModel):
    user_id: str
    book_id: str
    query: str
    chapter_limit: int


class QueryResponse(BaseModel):
    answer: str
    sources: List[str]


# === Endpoints ===

@app.get("/health")
def health_check():
    return {"status": "online", "db": "connected"}


@app.post("/v1/ingest", response_model=IngestResponse)
def ingest_book(file: UploadFile = File(...)):
    """Uploads a PDF, indexes it, and registers it in the DB."""

    # 1. Save File
    safe_filename = file.filename.replace(" ", "_")
    file_location = f"uploaded_{safe_filename}"

    with open(file_location, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # 2. Standardize name (Temporary: overwrites 'lord_of_mysteries.pdf')
    target_pdf = "lord_of_mysteries.pdf"
    if os.path.exists(target_pdf):
        try:
            os.remove(target_pdf)
        except OSError:
            pass
    shutil.move(file_location, target_pdf)

    # 3. Process
    print(f"⚙️ Ingesting: {safe_filename}...")
    try:
        env = os.environ.copy()
        subprocess.run([sys.executable, "ingest.py"], check=True, env=env)
        subprocess.run([sys.executable, "build_index.py"], check=True, env=env)
    except subprocess.CalledProcessError as e:
        raise HTTPException(status_code=500, detail=f"Ingestion failed: {e}")

    reload_index()

    # 4. Register in DB (The New Part!)
    # We assume it's 'Lord of the Mysteries' for now, but generated a unique ID
    book_id = database.register_book(
        title="Lord of the Mysteries",
        filename=safe_filename,
        index_path="semantic_index.faiss"
    )

    return {
        "message": "Book ingested and registered.",
        "book_id": book_id,
        "title": "Lord of the Mysteries"
    }


@app.post("/v1/query", response_model=QueryResponse)
def query_book(request: QueryRequest):
    """Answers questions using RAG + Conversation History from DB."""

    if not state.semantic_index:
        raise HTTPException(status_code=503, detail="Index not loaded.")

    # 1. Retrieve Chat History (Memory)
    # The 'memory' object passed to generate_answer needs a specific format.
    # We'll create a simple wrapper or pass the list directly if updated.
    history = database.get_chat_history(request.user_id, request.book_id)

    # Hack: We need to pass history to generate_answer.
    # Let's wrap it in a mock object since our generate_answer expects a .get_context() method
    class MemoryWrapper:
        def get_context(self, limit=6):
            return history

    memory_mock = MemoryWrapper()

    # 2. RAG Search
    raw_results = semantic_search(request.query, state.semantic_index, state.semantic_mapping)

    # 3. Filter Spoilers
    safe_results = []
    limit = request.chapter_limit
    for fname, chunk, _ in raw_results:
        try:
            chap_num = int(''.join(filter(str.isdigit, fname)))
            if chap_num <= limit:
                safe_results.append((fname, chunk))
        except ValueError:
            safe_results.append((fname, chunk))  # Keep safe if unknown

    final_context = safe_results[:3]
    chunks_text = [chunk for _, chunk in final_context]

    # 4. Generate Answer (With Memory!)
    answer = generate_answer(request.query, chunks_text, memory=memory_mock)

    # 5. Save to DB (Log the interaction)
    # Log User Question
    database.log_message(request.user_id, request.book_id, "user", request.query, request.chapter_limit)
    # Log Bot Answer
    database.log_message(request.user_id, request.book_id, "bot", answer, request.chapter_limit)

    return {
        "answer": answer,
        "sources": [f for f, _ in final_context]
    }
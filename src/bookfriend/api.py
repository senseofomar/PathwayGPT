import os
import shutil
import sys
import subprocess
from fastapi import FastAPI, HTTPException, UploadFile, File
from pydantic import BaseModel
from typing import List, Optional
from dotenv import load_dotenv

# Load secrets
load_dotenv()

# Import core logic
from utils.semantic_utils import load_semantic_index, semantic_search
from utils.answer_generator import generate_answer

# === Setup App ===
app = FastAPI(
    title="BookFriend API",
    version="2.0 (Stateless)",
    description="A stateless RAG API for the Quill reading platform."
)


# === Global State (Temporary until Phase 1, Step 3: Database) ===
# We still need to hold the loaded index in memory for speed.
class AppState:
    semantic_index = None
    semantic_mapping = None


state = AppState()


# === Startup ===
@app.on_event("startup")
def startup_event():
    print("⏳ API Startup: Loading Semantic Index...")
    reload_index()


def reload_index():
    try:
        idx, mapping = load_semantic_index()
        state.semantic_index = idx
        state.semantic_mapping = mapping
        print("✅ Index loaded successfully.")
    except Exception as e:
        print(f"⚠️ Index not found: {e}. Waiting for ingestion.")


# === API Contracts (The "Gemini" Style) ===

class IngestResponse(BaseModel):
    message: str
    book_id: str  # We return an ID so the client knows what to reference later


class QueryRequest(BaseModel):
    user_id: str  # Who is asking?
    book_id: str  # Which book are they talking about?
    query: str  # The question
    chapter_limit: int  # The Spoiler Shield (Passed PER REQUEST)


class QueryResponse(BaseModel):
    answer: str
    sources: List[str]


# === Endpoints ===

@app.get("/health")
def health_check():
    """Simple heartbeat for the Android app to check connection."""
    return {"status": "online", "version": "v1"}


@app.post("/v1/ingest", response_model=IngestResponse)
def ingest_book(file: UploadFile = File(...)):
    """
    Accepts a PDF, processes it, and returns a fixed book_id.
    (In Phase 1-Step-6 we will decouple this logic).
    """
    # 1. Save File
    file_location = f"uploaded_{file.filename}"
    with open(file_location, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # 2. Rename for internal pipeline (Temporary Assumption)
    target_pdf = "lord_of_mysteries.pdf"
    if os.path.exists(target_pdf):
        try:
            os.remove(target_pdf)
        except OSError:
            pass
    shutil.move(file_location, target_pdf)

    # 3. Trigger Processing
    print(f"⚙️ Processing book: {file.filename}")
    try:
        env = os.environ.copy()
        subprocess.run([sys.executable, "ingest.py"], check=True, env=env)
        subprocess.run([sys.executable, "build_index.py"], check=True, env=env)
    except subprocess.CalledProcessError as e:
        raise HTTPException(status_code=500, detail=f"Ingestion failed: {e}")

    # 4. Reload Brain
    reload_index()

    # Return a Mock ID for now (we will implement real IDs in the DB step)
    return {
        "message": "Book ingested successfully.",
        "book_id": "book_001_lotm"
    }


@app.post("/v1/query", response_model=QueryResponse)
def query_book(request: QueryRequest):
    """
    The main RAG endpoint.
    Stateless: Depends entirely on the 'chapter_limit' sent in the request.
    """
    if not state.semantic_index:
        raise HTTPException(status_code=503, detail="No book index loaded.")

    print(f"📨 Query from {request.user_id}: '{request.query}' [Limit: Ch {request.chapter_limit}]")

    # A. Search
    # Note: In the future, 'request.book_id' will tell us WHICH index to load.
    # For now, we use the single global index.
    raw_results = semantic_search(request.query, state.semantic_index, state.semantic_mapping, top_k=50)

    # B. Filter (Spoiler Shield)
    # Uses the request's specific limit, not a global variable!
    safe_results = []
    limit = request.chapter_limit

    for fname, chunk, dist in raw_results:
        try:
            chap_num = int(''.join(filter(str.isdigit, fname)))
            if chap_num <= limit:
                safe_results.append((fname, chunk))
        except ValueError:
            safe_results.append((fname, chunk))

    final_context = safe_results[:3]

    # C. Generate Answer
    # We pass 'None' for memory for now (Stateless).
    # Chat History will be handled by the DB in the next step.
    chunks_text = [chunk for _, chunk in final_context]

    try:
        answer = generate_answer(request.query, chunks_text, memory=None)
        return {
            "answer": answer,
            "sources": [fname for fname, _ in final_context]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
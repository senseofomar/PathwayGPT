import os
import shutil
import sys
import subprocess

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, UploadFile, File
from pydantic import BaseModel
from typing import List, Optional

# === Import your core logic ===
from utils.semantic_utils import load_semantic_index, semantic_search
from utils.answer_generator import generate_answer

load_dotenv()

# === 1. Setup App & State ===
app = FastAPI(title="BookFriend API (V1 Complete)", version="1.0")


class AppState:
    semantic_index = None
    semantic_mapping = None
    current_chapter_limit = 999999


state = AppState()


# === 2. Event Handlers ===
@app.on_event("startup")
def startup_event():
    print("⏳ API Startup: Loading Semantic Index...")
    reload_index()


def reload_index():
    """Helper to reload the AI brain after a new upload."""
    try:
        idx, mapping = load_semantic_index()
        state.semantic_index = idx
        state.semantic_mapping = mapping
        print("✅ Index loaded successfully.")
    except Exception as e:
        print(f"⚠️ Index not found: {e}. Waiting for upload.")


# === 3. Data Models ===
class AskRequest(BaseModel):
    query: str


class ProgressRequest(BaseModel):
    chapter_limit: int


class SearchResponse(BaseModel):
    answer: str
    sources: List[str]


# === 4. Endpoints ===

@app.get("/")
def home():
    return {
        "status": "online",
        "current_chapter_limit": state.current_chapter_limit,
        "brain_loaded": state.semantic_index is not None
    }


@app.post("/set-progress")
def set_progress(req: ProgressRequest):
    """Update the spoiler shield limit for this session."""
    state.current_chapter_limit = req.chapter_limit
    return {"message": f"Spoiler shield set to Chapter {req.chapter_limit}"}


@app.post("/upload")
def upload_book(file: UploadFile = File(...)):
    """
    1. Saves the PDF.
    2. Runs ingestion (extract text).
    3. Runs indexing (build vectors).
    4. Reloads the AI.
    """
    # A. Save the file
    file_location = f"uploaded_{file.filename}"
    with open(file_location, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    print(f"📥 Received file: {file_location}")

    # B. Trigger the pipeline (Ingest -> Index)
    # We rename the uploaded file to 'lord_of_mysteries.pdf' because your scripts expect that name.
    # (In V2 we will make this dynamic).
    target_pdf = "lord_of_mysteries.pdf"

    # Clean up old file if exists
    if os.path.exists(target_pdf):
        os.remove(target_pdf)

    # Rename uploaded file to target
    try:
        os.rename(file_location, target_pdf)
    except OSError:
        # Fallback for some windows file lock issues
        shutil.move(file_location, target_pdf)

    print("⚙️ Running Ingestion & Indexing...")
    try:
        # We run these as subprocesses to avoid import conflict headaches
        subprocess.run([sys.executable, "ingest.py"], check=True)
        subprocess.run([sys.executable, "build_index.py"], check=True)
    except subprocess.CalledProcessError as e:
        raise HTTPException(status_code=500, detail=f"Processing failed: {e}")

    # C. Reload the brain
    reload_index()

    return {"message": "Book processed and indexed! You can now ask questions."}


@app.post("/ask", response_model=SearchResponse)
def ask_question(request: AskRequest):
    if not state.semantic_index:
        raise HTTPException(status_code=503, detail="Index not loaded. Please /upload a book first.")

    limit = state.current_chapter_limit
    print(f"📨 Query: '{request.query}' | Shield: Ch {limit}")

    # A. Search (Fetch 50 candidates)
    raw_results = semantic_search(request.query, state.semantic_index, state.semantic_mapping, top_k=50)

    # B. Filter (Spoiler Shield)
    safe_results = []
    for fname, chunk, dist in raw_results:
        try:
            # Extract number from filename (e.g. "chapter_100.txt" -> 100)
            chap_num = int(''.join(filter(str.isdigit, fname)))
            if chap_num <= limit:
                safe_results.append((fname, chunk))
        except ValueError:
            safe_results.append((fname, chunk))

    final_context = safe_results[:3]

    if not final_context:
        return {
            "answer": f"Spoiler Shield Active! All matches were beyond Chapter {limit}.",
            "sources": []
        }

    # C. Generate Answer
    chunks_text = [chunk for _, chunk in final_context]
    try:
        answer = generate_answer(request.query, chunks_text)
        return {
            "answer": answer,
            "sources": [fname for fname, _ in final_context]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
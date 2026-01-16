import os
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional

# Import your actual logic
from utils.semantic_utils import load_semantic_index, semantic_search
from utils.answer_generator import generate_answer
from utils.config import SESSION_PATH
from utils import session_utils

# === 1. Setup App & State ===
app = FastAPI(title="BookFriend API", version="1.0")


# Global state to hold the heavy AI model (so we load it only once)
class AppState:
    semantic_index = None
    semantic_mapping = None


state = AppState()


# === 2. Event Handlers (Startup) ===
@app.on_event("startup")
def load_resources():
    """Load the heavy AI model when the server starts."""
    print("⏳ API Startup: Loading Semantic Index...")
    try:
        idx, mapping = load_semantic_index()
        state.semantic_index = idx
        state.semantic_mapping = mapping
        print("✅ Index loaded successfully.")
    except Exception as e:
        print(f"❌ Failed to load index: {e}")
        # We don't crash, but search won't work.


# === 3. Request Models (Strict Typing) ===
# This tells the API exactly what data to expect.
# Interview Win: "I use Pydantic for data validation."
class SearchRequest(BaseModel):
    query: str
    chapter_limit: Optional[int] = None  # The Spoiler Shield!


class SearchResponse(BaseModel):
    answer: str
    sources: List[str]  # List of filenames used


# === 4. Endpoints ===
@app.get("/")
def home():
    """Health check endpoint."""
    return {"status": "online", "message": "BookFriend API is running"}


@app.post("/ask", response_model=SearchResponse)
def ask_question(request: SearchRequest):
    """
    The main RAG endpoint.
    Receives a query + chapter limit -> Returns AI answer + sources.
    """
    if not state.semantic_index:
        raise HTTPException(status_code=503, detail="Semantic Index not loaded")

    print(f"📨 Received query: '{request.query}' (Limit: Ch {request.chapter_limit})")

    # A. Search (Fetch 50 to allow filtering)
    raw_results = semantic_search(request.query, state.semantic_index, state.semantic_mapping, top_k=50)

    # B. Spoiler Filter (Metadata Filtering)
    limit = request.chapter_limit if request.chapter_limit else 999999
    safe_results = []

    for fname, chunk, dist in raw_results:
        try:
            # Extract number from 'chapter_100.txt'
            chap_num = int(''.join(filter(str.isdigit, fname)))
            if chap_num <= limit:
                safe_results.append((fname, chunk))
        except ValueError:
            safe_results.append((fname, chunk))

    # Take top 3 SAFE chunks
    final_context = safe_results[:3]

    if not final_context:
        return {
            "answer": f"I found matches, but they were all beyond Chapter {limit}. No spoilers allowed! 🤫",
            "sources": []
        }

    # C. Generate Answer
    chunks_text = [chunk for _, chunk in final_context]
    try:
        # Note: We aren't using 'memory' here yet for simplicity (Stateless API for V1)
        answer = generate_answer(request.query, chunks_text)

        # Return structured JSON
        return {
            "answer": answer,
            "sources": [fname for fname, _ in final_context]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
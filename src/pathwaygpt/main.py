"""
PathwayGPT — Intelligent Semantic + Keyword Search CLI
------------------------------------------------------
This module orchestrates the main CLI flow for PathwayGPT.
It combines:
 - Semantic search using OpenAI embeddings.
 - Multi-keyword and fuzzy text search.
 - Context memory for follow-up queries.
 - Persistent sessions for user history and preferences.

Author: Omar Shaikh
"""

from dotenv import load_dotenv
import os
import sys

# === Environment Setup ===
load_dotenv()  # 🔑 Loads your .env file (contains API keys and config)

# === Internal Imports ===
from pathwaygpt.utils.command_router import handle_command
from pathwaygpt.utils.context_memory import recall_last_search, suggest_related
from pathwaygpt.memory import ChatMemory
from utils.collect_all_matches import collect_all_matches
from utils.config import CASE_SENSITIVE_MODE, SESSION_PATH, MAX_HISTORY
from utils.export_to_csv import export_to_csv
from utils.highlight import build_keyword_color_map, CHAPTERS_FOLDER
from utils.interactive_navigation import interactive_navigation
from utils import session_utils
from utils.semantic_utils import load_semantic_index, semantic_search
from utils.answer_generator import generate_answer


def main():
    """Main controller for PathwayGPT CLI."""
    # === Load or Initialize User Session ===
    session_data = session_utils.load_session(SESSION_PATH)
    session_data.setdefault("search_history", [])
    session_data.setdefault("total_search_count", 0)
    session_data.setdefault("favorites", [])
    chapter_range = session_data.get("chapter_range", None)
    search_this_session = 0

    # === Verify Chapter Data Directory ===
    script_dir = os.path.dirname(os.path.abspath(__file__))
    folder = os.path.join(script_dir, "chapters")
    if not os.path.isdir(folder):
        print(f"[❌ ERROR] Missing folder: {folder}")
        print("👉 Create a folder named 'chapters' next to this script and put your .txt chapter files inside.")
        sys.exit(1)

    # === Display Mode Info ===
    mode_label = "CASE-SENSITIVE" if CASE_SENSITIVE_MODE else "CASE-INSENSITIVE"
    print(f"\n📘 PathwayGPT — Multi-keyword & Semantic Search ({mode_label} mode)")
    print("💡 Type 'q' or 'quit' to exit, 'forget' to clear memory.\n")

    if session_data["search_history"]:
        print(f"📂 Previous session loaded. {len(session_data['search_history'])} past searches available.\n")

    # === Load Semantic Index for LLM Search ===
    semantic_index, semantic_mapping = load_semantic_index()

    # === Initialize Conversation Memory ===
    memory = ChatMemory(max_messages=10)

    # === CLI Main Loop ===
    while True:
        try:
            raw_input_val = input("\n🔍 Enter keyword(s) or command: ").strip()
        except EOFError:
            print("\n🛑 Input closed — exiting gracefully.")
            break
        except KeyboardInterrupt:
            print("\n🛑 Interrupted — saving session and exiting.")
            session_utils.save_session(session_data, SESSION_PATH)
            break

        # --- Empty Input Guard ---
        if not raw_input_val:
            print("⚠️ Please type something.")
            continue

        # --- Exit Command ---
        if raw_input_val.lower() in ("q", "quit", "exit"):
            session_utils.save_session(session_data, SESSION_PATH)
            print("👋 Goodbye — see you next time!")
            break

        # --- Handle Custom Commands (like 'set range', 'recall', etc.) ---
        handled, chapter_range = handle_command(
            raw_input_val,
            session_data,
            chapter_range,
            semantic_index,
            semantic_mapping,
            memory
        )

        # If command router fully handled the command, skip normal flow
        if handled == "exit":
            break
        elif handled:
            continue

        # --- Update Memory with Latest User Query ---
        memory.add("user", raw_input_val)
        context_preview = [m["content"] for m in memory.messages[-4:]]  # show last few interactions
        print(f"🧠 Context Snapshot: {context_preview}\n")

        # ======================================================
        # === SEMANTIC SEARCH MODE ===
        # ======================================================
        if raw_input_val.startswith("semantic:"):
            query = raw_input_val.split("semantic:", 1)[1].strip()

            # --- Perform Semantic Search ---
            results = semantic_search(query, semantic_index, semantic_mapping)
            if not results:
                print("⚠️ No semantic results found.")
                continue

            print("\n🔎 Top Semantic Matches:\n")
            for fname, chunk, dist in results[:5]:  # show top 5 snippets
                print(f"[{fname}] (similarity={dist:.2f}) → {chunk[:200]}...\n")

            # --- Prepare Context for Answer Generation ---
            top_chunks = [chunk for _, chunk, _ in results[:3]]

            print("\n🤖 PathwayGPT’s Interpretation:\n")
            print("🤔 Thinking...\n")

            # --- Try Generating Answer Using OpenAI ---
            try:
                answer = generate_answer(query, top_chunks, memory=memory)
                memory.add("assistant", answer)
                print(answer)
                print("\n✅ Done.\n")

            except Exception as e:
                print(f"⚠️ PathwayGPT couldn’t generate an answer: {e}")
                continue

            continue  # skip normal keyword mode after semantic search

        # ======================================================
        # === KEYWORD SEARCH MODE ===
        # ======================================================
        keywords = [k.strip() for k in raw_input_val.split(",") if k.strip()]
        if not keywords:
            print("⚠️ Please enter at least one keyword.")
            continue

        # --- Search Scope (All Chapters or Specific) ---
        mode = input("📂 Search in (a)ll chapters or (s)pecific? [a/s]: ").strip().lower()
        chapter_filter = None
        if mode == "s":
            chapter_filter = input("Enter part of chapter filename (e.g., 'chapter0005'): ").strip() or None

        # --- Suggest Related Past Keywords ---
        related = suggest_related(session_data, keywords)
        if related:
            print(f"💡 Related Past Keywords: {', '.join(related)}")

        # --- Ask User for Fuzzy Search ---
        use_fuzzy = input("Enable fuzzy search? (y/n): ").strip().lower() in ("y", "yes")

        # --- Update Session Stats ---
        search_this_session += 1
        session_data["total_search_count"] += 1
        session_data["search_history"].append((keywords, chapter_filter, use_fuzzy))
        if len(session_data["search_history"]) > MAX_HISTORY:
            session_data["search_history"].pop(0)

        # --- Restrict to Chapter Range (if user set one) ---
        valid_range = range(chapter_range[0], chapter_range[1] + 1) if chapter_range else None

        # --- Collect Keyword Matches Across Chapters ---
        matches = collect_all_matches(
            CHAPTERS_FOLDER,
            keywords,
            case_sensitive=CASE_SENSITIVE_MODE,
            fuzzy=use_fuzzy,
            chapter_filter=chapter_filter,
            valid_range=valid_range
        )

        if not matches:
            print("⚠️ No matches found for given keywords.")
            continue

        # --- Highlight and Navigate Results ---
        kw_color_map = build_keyword_color_map(keywords)
        interactive_navigation(matches, keywords, kw_color_map)

        # --- Export Results to CSV ---
        export_to_csv(matches, "recent_search_results.csv")
        print("\n📁 Exported: recent_search_results.csv")

        print("\n--- ✅ Search Finished ---\n")

        # --- Save Session After Each Search ---
        session_utils.save_session(session_data, SESSION_PATH)


# === Entry Point ===
if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\n💥 Fatal Error: {e}")
        sys.exit(1)

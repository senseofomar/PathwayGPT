import os
import sys

from pathwaygpt.utils.command_router import handle_command
from pathwaygpt.utils.context_memory import recall_last_search, suggest_related
from utils.collect_all_matches import collect_all_matches
from utils.config import CASE_SENSITIVE_MODE, SESSION_PATH, MAX_HISTORY
from utils.export_to_csv import export_to_csv
from utils.highlight import build_keyword_color_map, CHAPTERS_FOLDER
from utils.interactive_navigation import interactive_navigation
from utils import session_utils
from utils.semantic_utils import load_semantic_index, semantic_search
from utils.answer_generator import generate_answer
from pathwaygpt.memory import ChatMemory


def main():
    """Main controller for PathwayGPT CLI."""

    # === Load session ===
    session_data = session_utils.load_session(SESSION_PATH)
    session_data.setdefault("search_history", [])
    session_data.setdefault("total_search_count", 0)
    session_data.setdefault("favorites", [])
    chapter_range = session_data.get("chapter_range", None)
    search_this_session = 0

    # === Validate chapters folder ===
    script_dir = os.path.dirname(os.path.abspath(__file__))
    folder = os.path.join(script_dir, "chapters")
    if not os.path.isdir(folder):
        print(f"[ERROR] Missing folder: {folder}")
        print("Create a folder named 'chapters' next to this script and put .txt files inside.")
        sys.exit(1)

    # === Display mode ===
    mode_label = "CASE-SENSITIVE" if CASE_SENSITIVE_MODE else "CASE-INSENSITIVE"
    print(f"\nPathwayGPT — multi-keyword & semantic search ({mode_label} mode)")
    print("Type 'q' or 'quit' to exit.\n")

    if session_data["search_history"]:
        print(f"Previous session loaded. {len(session_data['search_history'])} past searches available.\n")

    # === Load Semantic Search Index ===
    semantic_index, semantic_mapping = load_semantic_index()

    # === Initialize Memory ===
    memory = ChatMemory(max_messages=10)

    # === Main Loop ===
    while True:
        try:
            raw_input_val = input("\n🔍 Enter keyword(s) or command: ").strip()
        except EOFError:
            print("\nInput closed — exiting.")
            break

        if not raw_input_val:
            print("Please type something.")
            continue

        # === Exit command ===
        if raw_input_val.lower() in ("q", "quit", "exit"):
            session_utils.save_session(session_data, SESSION_PATH)
            print("Goodbye — see you later.")
            break

        # === Handle Command ===
        handled, chapter_range = handle_command(
            raw_input_val,
            session_data,
            chapter_range,
            semantic_index,
            semantic_mapping
        )

        # if command_router handled the input fully
        if handled == "exit":
            break
        elif handled:
            continue

        # === Update short-term memory ===
        memory.add("user", raw_input_val)
        print(f"🧠 Context so far: {memory.get_context()}\n")

        # === Semantic Search Mode ===
        if raw_input_val.startswith("semantic:"):
            query = raw_input_val.split("semantic:", 1)[1].strip()
            results = semantic_search(query, semantic_index, semantic_mapping)

            if not results:
                print("⚠️ No semantic results found.")
                continue

            print("\n🔎 Semantic search results:\n")
            for fname, chunk, dist in results:
                print(f"[{fname}] (score={dist:.2f}) → {chunk[:200]}...\n")

            # Top chunks for context
            top_chunks = [chunk for _, chunk, _ in results[:3]]

            print("\n🤖 PathwayGPT’s interpretation:\n")
            answer = generate_answer(query, top_chunks)
            print(answer)
            continue

        # === Keyword Search Mode ===
        keywords = [k.strip() for k in raw_input_val.split(",") if k.strip()]
        if not keywords:
            print("Please enter at least one keyword.")
            continue

        mode = input("Search in (a)ll chapters or (s)pecific? [a/s]: ").strip().lower()
        chapter_filter = None
        if mode == "s":
            chapter_filter = input("Enter part of the chapter filename (e.g. 'chapter0005'): ").strip() or None

        related = suggest_related(session_data, keywords)
        if related:
            print(f"💡 Related past keywords: {', '.join(related)}")

        use_fuzzy = input("Enable fuzzy search? (y/n): ").strip().lower() in ("y", "yes")

        search_this_session += 1
        session_data["total_search_count"] += 1
        session_data["search_history"].append((keywords, chapter_filter, use_fuzzy))
        if len(session_data["search_history"]) > MAX_HISTORY:
            session_data["search_history"].pop(0)

        valid_range = range(chapter_range[0], chapter_range[1] + 1) if chapter_range else None

        matches = collect_all_matches(
            CHAPTERS_FOLDER,
            keywords,
            case_sensitive=CASE_SENSITIVE_MODE,
            fuzzy=use_fuzzy,
            chapter_filter=chapter_filter,
            valid_range=valid_range
        )

        if not matches:
            print("⚠️ No matches found.")
            continue

        kw_color_map = build_keyword_color_map(keywords)
        interactive_navigation(matches, keywords, kw_color_map)
        export_to_csv(matches, "recent_search_results.csv")

        print("\n--- Search finished ---\n")
        session_utils.save_session(session_data, SESSION_PATH)


if __name__ == "__main__":
    main()

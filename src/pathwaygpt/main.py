import os
import sys

from pathwaygpt.utils.context_memory import recall_last_search, suggest_related
from utils.collect_all_matches import collect_all_matches
from utils.config import CASE_SENSITIVE_MODE, SESSION_PATH, MAX_HISTORY
from utils.export_to_csv import export_to_csv
from utils.highlight import build_keyword_color_map, CHAPTERS_FOLDER
from utils.interactive_navigation import interactive_navigation
from utils import session_utils
from utils.semantic_utils import load_semantic_index, semantic_search
from utils.answer_generator import generate_answer  # ✅ moved import to top
from pathwaygpt.memory import ChatMemory


def main():
    """Main controller for PathwayGPT."""
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
    print(f"\n        PathwayGPT — multi-keyword search ({mode_label} mode)\n         (type 'q' or 'quit' to exit)\n")

    if session_data["search_history"]:
        print(f"Previous session loaded. {len(session_data['search_history'])} past searches available.\n")

    # === Load Semantic Search Index ===
    semantic_index, semantic_mapping = load_semantic_index()

    # === Initialize Memory ===
    memory = ChatMemory(max_messages=10)

    # === Main Loop ===
    while True:
        try:
            raw_input_val = input("\n🔍 Enter keyword(s) separated by commas (or 'q' to quit): ").strip()
        except EOFError:
            print("\nInput closed — exiting.")
            break

        if raw_input_val.lower() in ("q", "quit", "exit"):
            session_utils.save_session(session_data, SESSION_PATH)
            print("Goodbye — see you later.")
            break

        # === Update Memory ===
        memory.add("user", raw_input_val)
        print(f"🧠 Context so far: {memory.get_context()}\n")

        # === Command Handling ===
        command = raw_input_val.lower()

        if command == "search-history":
            if not session_data["search_history"]:
                print("No searches yet.")
            else:
                print("Last searches:")
                for i, (keys, chap, fuzzy) in enumerate(session_data["search_history"], 1):
                    chap_label = chap if chap else "all"
                    fuzzy_label = "fuzzy" if fuzzy else "exact"
                    print(f"{i}. {', '.join(keys)} [{chap_label}, {fuzzy_label}]")
            continue

        if command == "save-history-now":
            session_utils.save_session(session_data, SESSION_PATH)
            print("✅ Session saved.")
            continue

        if command == "clear-history":
            confirm = input("⚠️ Are you sure? (y/n): ")
            if confirm.lower() == "y":
                session_data["search_history"].clear()
                search_this_session = 0
                print("🧹 Search history cleared.\n")
            continue

        if command == "stats":
            print(f"📊 Total searches ever: {session_data['total_search_count']}")
            print(f"📊 Searches this session: {search_this_session}")
            print(f"📊 Saved history size: {len(session_data['search_history'])}\n")
            continue

        if command == "":
            print("Please type at least one keyword.")
            continue

        if command == "fav-add":
            if not session_data["search_history"]:
                print("⚠️ No search yet to add to favorites.")
            else:
                last_search = session_data["search_history"][-1]
                if last_search not in session_data["favorites"]:
                    session_data["favorites"].append(last_search)
                    print(f"✅ Added to favorites: {last_search}")
                else:
                    print("ℹ️ Already in favorites.")
            continue

        if command == "fav-list":
            if not session_data["favorites"]:
                print("⭐ No favorites yet.")
            else:
                print("\n⭐ Favorites:")
                for i, fav in enumerate(session_data["favorites"], 1):
                    keys, chap, fuzzy = fav
                    chap_label = chap if chap else "all"
                    fuzzy_label = "fuzzy" if fuzzy else "exact"
                    print(f"{i}. {', '.join(keys)} [{chap_label}, {fuzzy_label}]")
            continue

        if command == "set-range":
            try:
                raw = input("Enter start and end chapter (e.g., 1 50): ").strip()
                start, end = map(int, raw.split())
                chapter_range = [start, end]
                session_data["chapter_range"] = chapter_range
                session_utils.save_session(session_data, SESSION_PATH)
                print(f"✅ Range set: {start} → {end}")
            except Exception:
                print("⚠️ Invalid input. Example: 1 50")
            continue

        if command == "show-range":
            print(f"Current range: {chapter_range[0]} → {chapter_range[1]}" if chapter_range else "No range set.")
            continue

        if command == "clear-range":
            chapter_range = None
            session_data["chapter_range"] = None
            session_utils.save_session(session_data, SESSION_PATH)
            print("🗑️ Range cleared. Searching all chapters.")
            continue

        if command == "recall-last":
            last = recall_last_search(session_data)
            if not last:
                print("⚠️ No previous search found.")
            else:
                keys, chap, fuzzy = last
                print(f"Last search: {keys} [{chap or 'all'}, {'fuzzy' if fuzzy else 'exact'}]")
            continue

        # === SEMANTIC SEARCH + LLM ANSWER ===
        if command.startswith("semantic:"):
            query = raw_input_val.split("semantic:", 1)[1].strip()
            results = semantic_search(query, semantic_index, semantic_mapping)

            print("\n🔎 Semantic search results:\n")
            for fname, chunk, dist in results:
                print(f"[{fname}] (score={dist:.2f}) → {chunk[:200]}...\n")

            # Top 3 context chunks for generation
            top_chunks = [chunk for _, chunk, _ in results[:3]]

            print("\n🤖 PathwayGPT’s interpretation:\n")
            answer = generate_answer(query, top_chunks)
            print(answer)
            continue

        # === KEYWORD SEARCH MODE ===
        keywords = [k.strip() for k in raw_input_val.split(",") if k.strip()]
        mode = input("Search in (a)ll chapters or (s)pecific? [a/s]: ").strip().lower()
        chapter_filter = input("Enter part of the chapter filename (e.g. 'chapter0005'): ").strip() if mode == "s" else None

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

import os  # 'os' module: lets us work with the operating system (folders, files, paths, etc.).
import sys  # 'sys' module: lets us access system-specific functionality (like exiting the script early).

from utils.collect_all_matches import collect_all_matches
from utils.config import CASE_SENSITIVE_MODE
from utils.export_to_csv import export_to_csv
from utils.highlight import build_keyword_color_map, CHAPTERS_FOLDER
from utils.interactive_navigation import interactive_navigation
from utils import session_utils

SESSION_PATH = "session.json"
# =========================
# FUNCTION: main
# =========================
def main():
    """
    Main program controller.
    - Finds the 'chapters' folder.
    - Keeps asking the user for keywords.
    - Searches through chapter files until the user quits.
    """


    search_history = []                  #for user search history


    # Get the directory where this script is located.
    script_dir = os.path.dirname(os.path.abspath(__file__))

    # Build the path to the "chapters" folder in the same directory as the script.
    folder = os.path.join(script_dir, "chapters")

    # If the folder doesn't exist, inform the user and stop the program.
    if not os.path.isdir(folder):
        print(f"[ERROR] Missing folder: {folder}")
        print("Create a folder named 'chapters' next to this script and put .txt files inside.")
        sys.exit(1)  # Exit the script with status code 1 (indicates error).

    #load previous session
    session_data = session_utils.load_session(SESSION_PATH)
    print("previous session:", session_data)

    # Display program mode (case-sensitive or not) to the user.
    mode_label = "CASE-SENSITIVE" if CASE_SENSITIVE_MODE else "CASE-INSENSITIVE"
    print(f"PathwayGPT — multi-keyword search ({mode_label} mode)\n(type 'q' or 'quit' to exit)\n")

    # Main input loop — keeps running until user quits.
    while True:
        try:
            # Ask user for comma-separated keywords.
            raw_input_val = input("🔍 Enter keyword(s) separated by commas (or 'q' to quit): ").strip()
        except EOFError:
            # EOFError occurs when input is closed (e.g., Ctrl+D in Unix).
            print("\nInput closed — exiting.")
            break

        if raw_input_val.lower() in ("q", "quit", "exit"):
            print("Goodbye — see you later.")
            break

        if raw_input_val.lower() == "search-history":
            if not search_history:
                print("No searches yet.")
            else:
                print("Last searches:")
                for i, (keys, chap, fuzzy) in enumerate(search_history, 1):
                    chap_label = chap if chap else "all"
                    fuzzy_label = "fuzzy" if fuzzy else "exact"
                    print(f"{i}. {', '.join(keys)} [{chap_label}, {fuzzy_label}]")
            continue

        if raw_input_val == "":
            print("Please type at least one keyword.")
            continue

         # Split input by commas → strip spaces → remove empty results.
        keywords = [k.strip() for k in raw_input_val.split(",") if k.strip()]

        # Step 1: Ask global vs chapter-specific
        chapter_filter = None
        mode = input("Search in (a)ll chapters or (s)pecific? [a/s]: ").strip().lower()
        if mode == "s":
            chapter_filter = input("Enter part of the chapter filename (e.g. 'chapter0005'): ").strip()

        # Step 2: Fuzzy choice
        use_fuzzy = input("Enable fuzzy search? (y/n): ").strip().lower() in ("y", "yes")

        # Save to history
        search_history.append((keywords, chapter_filter, use_fuzzy))
        if len(search_history) > 3:
            search_history.pop(0)

        # Step 3: Collect matches
        matches = collect_all_matches(
            CHAPTERS_FOLDER,
            keywords,
            case_sensitive=CASE_SENSITIVE_MODE,
            fuzzy=use_fuzzy,
            chapter_filter=chapter_filter
        )

        if not matches:
            print("⚠️ No matches found.")
            continue

        #Build per-keyword color mapping for consistent coloring
        kw_color_map = build_keyword_color_map(keywords)


        #Enter interactive navigation UI
        interactive_navigation(matches, keywords, kw_color_map)


        export_to_csv(matches, 'recent_search_results.csv')

        session_utils.save_session(session_data, SESSION_PATH)
        # Separator after search results.
        print("\n--- Search finished ---\n")

# =========================
# RUN PROGRAM
# =========================
if __name__ == "__main__":
    # This block runs only if script is executed directly (not imported as a module).
    main()

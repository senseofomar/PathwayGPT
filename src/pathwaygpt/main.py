import os  # 'os' module: lets us work with the operating system (folders, files, paths, etc.).
import sys  # 'sys' module: lets us access system-specific functionality (like exiting the script early).

from collect_all_matches import collect_all_matches
from config import CASE_SENSITIVE_MODE
from export_to_csv import export_to_csv
from highlight import build_keyword_color_map, CHAPTERS_FOLDER
from interactive_navigation import interactive_navigation

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

        # Exit commands — check lowercase version for flexibility.
        if raw_input_val.lower() in ("q", "quit", "exit"):
            print("Goodbye — see you later.")
            break

        # Empty input handling.
        if raw_input_val == "":
            print("Please type at least one keyword.")
            continue

        #Search history
        if raw_input_val.lower() == "search-history":
            if not search_history:
                print("No searches yet.")
            else:
                print("Last searches:")
                for i, h in enumerate(search_history, 1):
                    print(f"{i}. {', '.join(h)}")
            continue  # go back to input loop

        # Split input by commas → strip spaces → remove empty results.
        keywords = [k.strip() for k in raw_input_val.split(",") if k.strip()]

        # 4) Build per-keyword color mapping for consistent coloring
        kw_color_map = build_keyword_color_map(keywords)

        # fuzzy searching

        use_fuzzy = input("Enable fuzzy search? (y/n): ").strip().lower() in ("y", "yes")

        matches = collect_all_matches(
            CHAPTERS_FOLDER,
            keywords,
            case_sensitive=CASE_SENSITIVE_MODE,
            fuzzy=use_fuzzy
        )

        # 5) Collect matches across all chapter files (may take a moment for many files)
        print("Collecting matches across chapter files (this may take a moment)...")
        #matches = collect_all_matches(CHAPTERS_FOLDER, keywords)  used previously


        # 6) Enter interactive navigation UI
        interactive_navigation(matches, keywords, kw_color_map)

        search_history.append(keywords)
        if len(search_history) > 3:
            search_history.pop(0)  # remove oldest

        # Separator after search results.
        print("\n--- Search finished ---\n")

        export_to_csv(matches, 'recent_search_results.csv')


# =========================
# RUN PROGRAM
# =========================
if __name__ == "__main__":
    # This block runs only if script is executed directly (not imported as a module).
    main()

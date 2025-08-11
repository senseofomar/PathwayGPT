# =========================
# IMPORTS
# =========================

import os  # 'os' module: lets us work with the operating system (folders, files, paths, etc.).
import sys  # 'sys' module: lets us access system-specific functionality (like exiting the script early).
import re # 're' module: Python's Regular Expressions — powerful pattern matching for text.
from config import CASE_SENSITIVE_MODE
from search import search_in_chapters


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
    print(f"GrayFogGPT Day1 — multi-keyword search ({mode_label} mode)\n(type 'q' or 'quit' to exit)\n")

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

        # Split input by commas → strip spaces → remove empty results.
        keywords = [k.strip() for k in raw_input_val.split(",") if k.strip()]

        # Perform the search in the "chapters" folder.
        search_in_chapters(folder, keywords)

        # Separator after search results.
        print("\n--- Search finished ---\n")

# =========================
# RUN PROGRAM
# =========================
if __name__ == "__main__":
    # This block runs only if script is executed directly (not imported as a module).
    main()

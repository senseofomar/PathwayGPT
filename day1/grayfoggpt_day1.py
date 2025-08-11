# =========================
# IMPORTS
# =========================

import os  # 'os' lets us interact with the operating system: work with files, folders, and paths.
import re  # 're' is Python's Regular Expression library — allows advanced text search and pattern matching.
import sys  # 'sys' provides system-level operations, e.g., sys.exit() to stop the program.

# =========================
# SETTINGS — Change here to switch modes
# =========================

# CASE_SENSITIVE_MODE is a global setting that controls search behavior.
# True  → matches must exactly match letter case (e.g., "Main" != "main").
# False → ignores case differences (e.g., "Main" == "main" == "MAIN").
CASE_SENSITIVE_MODE = False


# =========================
# FUNCTION: keyword_in_sentence
# =========================
def keyword_in_sentence(keyword, sentence):
    """
    Return True if the 'keyword' appears in 'sentence' as a WHOLE WORD.

    Whole word means:
        - 'main' will match 'main'
        - 'main' will NOT match 'remained'

    Respects the global CASE_SENSITIVE_MODE setting for case behavior.
    """

    # Step 1: Create a regex pattern with word boundaries (\b) to match the whole word.
    # re.escape(keyword) ensures any special regex characters in the keyword are treated literally.
    pattern = r'\b' + re.escape(keyword) + r'\b'

    # Step 2: Decide case-sensitivity based on global setting.
    # flags = 0 → exact case match; re.IGNORECASE → match regardless of case.
    flags = 0 if CASE_SENSITIVE_MODE else re.IGNORECASE

    # Step 3: Search the sentence for our pattern.
    # re.search() returns a Match object if found, None otherwise.
    # bool(...) converts the result into True/False.
    return bool(re.search(pattern, sentence, flags))


# =========================
# FUNCTION: search_in_chapters
# =========================
def search_in_chapters(folder_path, keyword):
    """
    Search for a keyword inside all .txt files in folder_path and print matching sentences.

    Parameters:
        folder_path (str) - path to the folder containing text files.
        keyword (str)     - the word or phrase we want to find.
    """

    # Tracks whether at least one match was found across all files.
    found_any = False

    # Step 1: Loop through files in the folder in sorted order for consistent output.
    for filename in sorted(os.listdir(folder_path)):

        # Step 2: Only process files ending with ".txt" (case-insensitive check).
        if filename.lower().endswith(".txt"):
            file_path = os.path.join(folder_path, filename)  # Full path to file.

            try:
                # Step 3: Open the file for reading in UTF-8 encoding.
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()
            except Exception as e:
                # If file can’t be opened/read, display an error and skip it.
                print(f"[ERROR] Could not read '{file_path}': {e}")
                continue

            # Step 4: Quick first check — skip file if keyword not found anywhere in it.
            # Saves time instead of splitting into sentences unnecessarily.
            if keyword_in_sentence(keyword, content):
                found_any = True
                print(f"\n=== Matches in {filename} ===")

                # Step 5: Split file content into sentences.
                # Regex: '(?<=[.!?])\s+' means "split at spaces that follow . or ! or ?".
                sentences = re.split(r'(?<=[.!?])\s+', content)

                # Step 6: Check each sentence for the keyword.
                for sentence in sentences:
                    if keyword_in_sentence(keyword, sentence):
                        # Print sentence with leading "➜" for visual clarity.
                        print("  ➜", sentence.strip())

    # Step 7: If nothing was found in any file, display message.
    if not found_any:
        print(f"\nNo matches found for '{keyword}' in folder '{folder_path}'.")


# =========================
# FUNCTION: main
# =========================
def main():
    """
    Main driver function — sets up the environment and runs the search loop.
    """

    # Step 1: Find the directory where this script is located.
    script_dir = os.path.dirname(os.path.abspath(__file__))

    # Step 2: Look for a "chapters" folder next to this script.
    folder = os.path.join(script_dir, "chapters")

    # Step 3: If folder doesn't exist, display error and exit.
    if not os.path.isdir(folder):
        print(f"[ERROR] Missing folder: {folder}")
        print("Create a folder named 'chapters' next to this script and put .txt files inside.")
        sys.exit(1)  # Exit program.

    # Step 4: Display program intro with mode information.
    mode_label = "CASE-SENSITIVE" if CASE_SENSITIVE_MODE else "CASE-INSENSITIVE"
    print(f"GrayFogGPT Day1 — keyword search ({mode_label} mode)\n(type 'q' or 'quit' to exit)\n")

    # Step 5: Infinite loop for user input until they quit.
    while True:
        try:
            # Prompt for keyword.
            keyword = input("🔍 Enter a keyword (or 'q' to quit): ").strip()
        except EOFError:
            # If input is unexpectedly closed (e.g., Ctrl+D), exit cleanly.
            print("\nInput closed — exiting.")
            break

        # Step 6: Quit command check.
        if keyword.lower() in ("q", "quit", "exit"):
            print("Goodbye — see you later.")
            break

        # Step 7: Reject empty input.
        if keyword == "":
            print("Please type a non-empty keyword.")
            continue

        # Step 8: Perform search in all chapter files.
        search_in_chapters(folder, keyword)

        # Step 9: Print a separator after each search.
        print("\n--- Search finished ---\n")


# =========================
# RUN PROGRAM
# =========================
if __name__ == "__main__":
    # This check ensures that main() runs only if this script is executed directly,
    # not if it’s imported as a module from another script.
    main()

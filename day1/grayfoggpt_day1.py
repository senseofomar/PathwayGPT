import os     # 'os' lets us work with files and folders (listing, joining paths, etc.)
import re     # 're' is Python's Regular Expression library — for text pattern matching/splitting.
import sys    # 'sys' gives us system-level tools (like exiting the program with sys.exit()).

# =========================
# Function: search_in_chapters
# =========================
def search_in_chapters(folder_path, keyword, case_insensitive=True):
    """
    Search for a keyword inside all .txt files in folder_path and print matching sentences.

    Parameters:
        folder_path (str)       - path to the folder containing text files
        keyword (str)           - the word or phrase we want to find
        case_insensitive (bool) - whether to ignore uppercase/lowercase differences
    """

    # Prepare a "search version" of the keyword
    # If case_insensitive is True, we lowercase the keyword so comparisons are easier.
    # This prevents missing matches just because of uppercase/lowercase differences.
    if case_insensitive:
        kw = keyword.lower()
    else:
        kw = keyword

    found_any = False  # Tracks if we find *any* match at all (used for final "no matches" message).

    # Loop through all files in the folder — sorted() ensures results are always in the same order.
    for filename in sorted(os.listdir(folder_path)):
        # Only process files ending in .txt (case-insensitive check)
        if filename.lower().endswith(".txt"):
            file_path = os.path.join(folder_path, filename)  # Create the full file path.

            try:
                # Open the file safely with UTF-8 encoding (good for most text).
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()  # Read the whole file into one big string.
            except Exception as e:
                # If opening/reading fails, print an error but don't crash the program.
                print(f"[ERROR] Could not read '{file_path}': {e}")
                continue  # Move on to the next file.

            # Prepare the file's content for searching:
            # If case-insensitive, lowercase the whole content so "Fog" == "fog".
            search_content = content.lower() if case_insensitive else content

            # Check if our keyword exists anywhere in the text.
            if kw in search_content:
                found_any = True  # Mark that we found something.
                print(f"\n=== Matches in {filename} ===")  # Header for this file's matches.

                # Split the text into sentences.
                # This regex: r'(?<=[.!?])\s+' means:
                #   - '(?<=[.!?])' → look for a position *after* ., !, or ?
                #   - '\s+' → then match one or more spaces/newlines
                # This gives us separate sentences based on punctuation.
                sentences = re.split(r'(?<=[.!?])\s+', content)

                # Loop over each sentence to check for the keyword.
                for sentence in sentences:
                    # Prepare the sentence for matching (lowercase if case-insensitive)
                    check_sentence = sentence.lower() if case_insensitive else sentence
                    if kw in check_sentence:
                        # If the keyword exists here, print the sentence without extra spaces.
                        print("  ➜", sentence.strip())

    # After checking all files: if we found nothing, say so.
    if not found_any:
        print(f"\nNo matches found for '{keyword}' in folder '{folder_path}'.")


# =========================
# Function: main
# =========================
def main():
    """
    Main entry point for the program.
    - Figures out where the 'chapters' folder is.
    - Runs a loop asking the user for keywords until they quit.
    """

    # Find the folder 'chapters' that should be NEXT TO this script file.
    # __file__ is the path of the current Python file.
    script_dir = os.path.dirname(os.path.abspath(__file__))  # Folder containing this script.
    folder = os.path.join(script_dir, "chapters")  # Append 'chapters' to that folder path.

    # If the 'chapters' folder doesn't exist, tell the user and quit cleanly.
    if not os.path.isdir(folder):
        print(f"[ERROR] Missing folder: {folder}")
        print("Create a folder named 'chapters' next to this script and put .txt files inside.")
        sys.exit(1)  # Exit the program with status code 1 (means 'error').

    # Print a small program header.
    print("GrayFogGPT Day1 — simple keyword search (type 'q' or 'quit' to exit)\n")

    # =========================
    # Interactive Search Loop
    # =========================
    while True:
        try:
            # Ask the user for a keyword — .strip() removes leading/trailing spaces.
            keyword = input("🔍 Enter a keyword (or 'q' to quit): ").strip()
        except EOFError:
            # Handles the case when the input stream closes unexpectedly
            # (e.g., pressing Ctrl+D in Linux/Mac).
            print("\nInput closed — exiting.")
            break  # Exit the loop.

        # If the user typed q, quit, or exit (case-insensitive), stop the program.
        if keyword.lower() in ("q", "quit", "exit"):
            print("Goodbye — see you later.")
            break

        # If the user pressed Enter without typing anything, ask again.
        if keyword == "":
            print("Please type a non-empty keyword.")
            continue

        # For now, we *always* do case-insensitive search (good for testing).
        search_in_chapters(folder, keyword, case_insensitive=True)

        # Print a separator so results are visually clearer between searches.
        print("\n--- Search finished ---\n")


# =========================
# Script entry point check
# =========================
if __name__ == "__main__":
    # This makes sure main() only runs if we run THIS file directly
    # and not if we import it into another Python file.
    main()

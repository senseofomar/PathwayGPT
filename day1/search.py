# =========================
# FUNCTION: search_in_chapters
# =========================
import os
import re # 're' module: Python's Regular Expressions — powerful pattern matching for text.

from highlight import highlight_keywords
from utils import keyword_in_sentence


def search_in_chapters(folder_path, keywords):
    """
    Searches for all given keywords inside all .txt files in the given folder.
    Prints out only the sentences containing matches, with keywords highlighted.
    """
    found_any = False  # Keeps track of whether we found at least one match in any file.

    # Go through all files in the folder in sorted order (alphabetical for consistency).
    for filename in sorted(os.listdir(folder_path)):
        # Only process files ending in ".txt" (case-insensitive check).
        if filename.lower().endswith(".txt"):
            # Build the full file path by joining folder path with file name.
            file_path = os.path.join(folder_path, filename)

            # Attempt to open and read the file.
            try:
                # Always use UTF-8 encoding to avoid errors with special characters.
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()
            except Exception as e:
                # If reading fails (permissions, missing file, etc.), print error and skip.
                print(f"[ERROR] Could not read '{file_path}': {e}")
                continue

            # Quick scan: If file contains no keyword at all, skip further processing.
            if keyword_in_sentence(keywords, content):
                found_any = True  # At least one match found somewhere.

                # Print a header for matches in this file.
                print(f"\n=== Matches in {filename} ===")

                # Split text into sentences based on punctuation (., !, ? followed by space).
                sentences = re.split(r'(?<=[.!?])\s+', content)

                # Check each sentence individually.
                for sentence in sentences:
                    if keyword_in_sentence(keywords, sentence):
                        # Highlight all keywords in that sentence.
                        highlighted = highlight_keywords(sentence, keywords)
                        # Print with an arrow for readability.
                        print("  ➜", highlighted.strip())

    # After checking all files, if nothing was found in any file, notify the user.
    if not found_any:
        print(f"\nNo matches found for {', '.join(keywords)} in folder '{folder_path}'.")

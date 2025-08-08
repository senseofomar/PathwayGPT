import os
import re


def search_in_chapters(folder_path, keyword, case_insensitive=True):
    """Search for a keyword inside all .txt files in the given folder."""
    if case_insensitive:
        keyword = keyword.lower()

    for filename in os.listdir(folder_path):
        if filename.endswith(".txt"):
            file_path = os.path.join(folder_path, filename)
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
                search_content = content.lower() if case_insensitive else content
                if keyword in search_content:
                    print(f"✅ Keyword '{keyword}' found in {filename}")
                    # Split into sentences (handles ., ?, !)
                    sentences = re.split(r'(?<=[.!?])\s+', content)

                    for sentence in sentences:
                        # Check in lowercase version if case-insensitive
                        check_sentence = sentence.lower() if case_insensitive else sentence
                        if keyword in check_sentence:
                            print(f"  ➡ {sentence.strip()}")
                else:
                    print(f"❌ Keyword '{keyword}' NOT found in {filename}")


def main():
    # Get the folder path relative to THIS script
    script_dir = os.path.dirname(os.path.abspath(__file__))
    folder = os.path.join(script_dir, "chapters")

    keyword = input("🔍 Enter a keyword to search: ")
    case_insensitive = input("Case-insensitive search? (y/n): ").lower() == "y"

    search_in_chapters(folder, keyword, case_insensitive)


if __name__ == "__main__":
   main()
import os
import re  # "re" stands for Regular Expressions (used to find patterns like 'Chapter 1')
from pypdf import PdfReader

# Configuration
PDF_PATH = "lord_of_mysteries.pdf"  # Make sure this file is in your bookfriend folder
OUTPUT_FOLDER = "chapters"
MIN_CHAPTER_LENGTH = 500  # Filter: If text is shorter than this, it's likely a TOC entry or noise.

def ingest_pdf(pdf_path, output_folder):
    # 1. Validation: Does the file actually exist?
    if not os.path.exists(pdf_path):
        print(f"❌ Error: File not found at {pdf_path}")
        return

    # 2. Create the output folder if it doesn't exist (Engineer mindset: Handle setup automatically)
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)
        print(f"📂 Created folder: {output_folder}")

    print(f"📖 Reading {pdf_path}...")

    try:
        reader = PdfReader(pdf_path)
        full_text = ""

        # 3. Extraction: Loop through every page and stack the text
        # enumerate gives us a counter (i) and the page object
        for i, page in enumerate(reader.pages):
            text = page.extract_text()
            if text:
                full_text += text + "\n"  # Add a newline so words don't mash together

            # optional: simple progress indicator
            if i % 50 == 0:
                print(f"   ...processed {i} pages")

        print(f"✅ Text extraction complete. Total length: {len(full_text)} characters.")

        # 4. Parsing: Split the massive text block into Chapters
        # Regex Explanation:
        # r"Chapter \d+" means: Look for the word "Chapter" followed by a space and one or more digits (0-9).
        # We split the text every time we see that pattern.
        # Improved Regex: Handles multiple spaces or newlines between "Chapter" and the number
        # r"Chapter\s+\d+" -> "Chapter" + (one or more spaces/tabs/newlines) + digits
        pattern = r'(Chapter\s+\d+)'
        chapters = re.split(pattern, full_text, flags=re.IGNORECASE)

        # The split creates a list like: ['', 'Chapter 1', 'Text...', 'Chapter 2', 'Text...']
        # We need to pair the Chapter Title with its Content.

        saved_count = 0

        # We start from 1 because the first element is usually empty text before the first chapter
        for i in range(1, len(chapters), 2):
            chapter_title = chapters[i].strip()  # e.g., "Chapter 1"
            chapter_content = chapters[i + 1].strip()  # The actual story text

            # --- 🛡️ THE FIX: FILTER JUNK ---
            if len(chapter_content) < MIN_CHAPTER_LENGTH:
                print(
                    f"   ⚠️ Skipping '{chapter_title}' (Content too short: {len(chapter_content)} chars) -> Likely Table of Contents")
                continue

            # Clean filename: "Chapter 1" -> "chapter_001.txt"
            # Extract just the number to format it nicely
            try:
                # Find the number in the title string
                number = re.search(r'\d+', chapter_title).group()
                safe_title = f"chapter_{int(number):03d}"
            except:
                # Fallback if something weird happens
                safe_title = chapter_title.replace(" ", "_").lower()

            filename = f"{safe_title}.txt"
            file_path = os.path.join(output_folder, filename)

            # Save
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(chapter_title + "\n\n" + chapter_content)

            saved_count += 1

        print(f"🎉 Success! Extracted {saved_count} chapters into '{output_folder}/'.")

    except Exception as e:
        print(f"💥 Something went wrong: {e}")


# This block ensures the code only runs if you execute this file directly
if __name__ == "__main__":
    ingest_pdf(PDF_PATH, OUTPUT_FOLDER)
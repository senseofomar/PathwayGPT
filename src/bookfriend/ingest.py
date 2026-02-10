import os
import sys
import shutil
import re
from pypdf import PdfReader

# === Configuration ===
if len(sys.argv) > 2:
    PDF_PATH = sys.argv[1]
    OUTPUT_FOLDER = sys.argv[2]
else:
    # Developer Fallback (Only runs if you execute manually)
    PDF_PATH = "lord_of_mysteries.pdf"
    OUTPUT_FOLDER = "chapters"

MIN_CHAPTER_LENGTH = 500

def ingest_pdf(pdf_path, output_folder):
    if not os.path.exists(pdf_path):
        print(f"❌ Error: File not found at {pdf_path}")
        return

    # === SAFETY FIX: Only delete/create folder INSIDE the function ===
    if os.path.exists(output_folder):
        shutil.rmtree(output_folder)
    os.makedirs(output_folder)
    print(f"📂 Created folder: {output_folder}")

    print(f"📖 Reading {pdf_path}...")
    try:
        reader = PdfReader(pdf_path)
        full_text = ""
        for i, page in enumerate(reader.pages):
            text = page.extract_text()
            if text:
                full_text += text + "\n"

        # 1. Try splitting by "Chapter X"
        pattern = r'(Chapter\s+\d+)'
        chapters = re.split(pattern, full_text, flags=re.IGNORECASE)

        saved_count = 0

        # If regex worked (found more than just the start), process chapters
        if len(chapters) > 1:
            for i in range(1, len(chapters), 2):
                chapter_title = chapters[i].strip()
                chapter_content = chapters[i + 1].strip()

                if len(chapter_content) < MIN_CHAPTER_LENGTH:
                    continue

                try:
                    number = re.search(r'\d+', chapter_title).group()
                    safe_title = f"chapter_{int(number):03d}"
                except:
                    safe_title = chapter_title.replace(" ", "_").lower()

                filename = f"{safe_title}.txt"
                with open(os.path.join(output_folder, filename), "w", encoding="utf-8") as f:
                    f.write(chapter_title + "\n\n" + chapter_content)
                saved_count += 1

        # === 🛡️ FALLBACK MODE (The Fix) ===
        # If we found 0 chapters (maybe it says "Night 1" or has no headers),
        # just save the whole thing as one file. The Indexer will chunk it anyway.
        if saved_count == 0:
            print("⚠️ No 'Chapter X' headings found. Switching to Fallback Mode (Saving full text).")
            filename = "full_text.txt"
            with open(os.path.join(output_folder, filename), "w", encoding="utf-8") as f:
                f.write(full_text)
            saved_count = 1

        print(f"🎉 Success! Extracted {saved_count} text chunks into '{output_folder}/'.")

    except Exception as e:
        print(f"💥 Something went wrong: {e}")

if __name__ == "__main__":
    # Only run logic if this file is the main program
    print(f"📄 Ingesting: {PDF_PATH}")
    print(f"📂 Output: {OUTPUT_FOLDER}")
    ingest_pdf(PDF_PATH, OUTPUT_FOLDER)
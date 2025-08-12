
# ============================================
# Interactive multi-keyword search with:
#  - distinct colors per keyword
#  - context preview (snippet around the match)
#  - list of matches (file + snippet)
#  - interactive navigation: n (next), p (prev), number (jump), o (open in editor), q (quit)

# -----------------------
# IMPORTS — required modules
# -----------------------
import os                         # for file and path handling, launching OS commands
import re                         # for regex searching and substitution
import sys                        # for sys.exit and platform detection
import subprocess                 # for launching external programs (like editor)
from collections import namedtuple  # for simple structured storage (Match records)
from shutil import which          # to check if an executable exists on PATH

# Attempt to import colorama so colored output works on Windows.
# If colorama isn't installed, the script will still run but without colors.
try:
    from colorama import Fore, Style, init as colorama_init
except Exception:
    Fore = None
    Style = None

# Initialize colorama if available so colors reset properly on Windows terminals.
# If colorama not present, this call will be skipped (we check above).
if Fore and Style:
    colorama_init(autoreset=True)

# -----------------------
# CONFIGURATION - change these as needed
# -----------------------

# The relative path to the folder that contains your chapter text files.
# It is built relative to this script's location so the script can be run from anywhere.
CHAPTERS_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), "chapters")

# How many characters before/after the match to show in the snippet preview.
# This is an approximate context window to help you understand where the match sits.
CONTEXT_CHARS = 40

# List of ANSI color names we'll cycle through for keywords (if colorama available).
# The mapping below maps these names to actual Fore.* color codes.
_COLOR_LIST = ["RED", "GREEN", "YELLOW", "BLUE", "MAGENTA", "CYAN"]

# If you prefer a different command to open PyCharm, change this variable.
# Typical name for the PyCharm command-line launcher is 'charm'.
# You can create it in PyCharm: Tools → Create Command-line Launcher... → name 'charm'
PYCHARM_LAUNCHER_CMD = "charm"

# -----------------------
# Helper: COLOR_MAP — map friendly names to colorama Fore constants (or empty string fallback)
# -----------------------
if Fore:
    COLOR_MAP = {
        "RED": Fore.RED, "GREEN": Fore.GREEN, "YELLOW": Fore.YELLOW,
        "BLUE": Fore.BLUE, "MAGENTA": Fore.MAGENTA, "CYAN": Fore.CYAN
    }
else:
    # Fallback: if colorama isn't installed, use empty strings so printed text is plain.
    COLOR_MAP = {name: "" for name in _COLOR_LIST}
    # Provide a minimal Style-like object so Style.RESET_ALL usage won't crash.
    class _DummyStyle:
        RESET_ALL = ""
    Style = _DummyStyle()

# -----------------------
# Data container: Match
# -----------------------
# Using namedtuple to keep matched item data organized and readable.
Match = namedtuple("Match", [
    "file",     # filename where match occurred (e.g., 'chapter0001.txt')
    "sentence", # full sentence text containing the match (original unmodified)
    "start",    # start character index of the match within the sentence (int)
    "end",      # end character index of the match within the sentence (int)
    "keyword",  # the keyword string that matched (from user input)
    "snippet"   # short snippet string built around the match for preview
])

# -----------------------
# Helper functions (small, focused, well-commented)
# -----------------------

def build_keyword_color_map(keywords):
    """
    Assign a color to each keyword, cycling through available colors.
    Returns a dict {keyword: color_code_or_empty_string}.
    Why: So the same keyword is displayed consistently in the same color everywhere.
    """
    mapping = {}
    color_names = list(COLOR_MAP.keys())
    for i, kw in enumerate(keywords):
        # choose color by cycling index modulo number of available colors
        color_name = color_names[i % len(color_names)]
        mapping[kw] = COLOR_MAP[color_name]
    return mapping


def whole_word_pattern(keyword):
    """
    Build a regex pattern that matches 'keyword' as a whole word.
    Uses re.escape to make the keyword safe if it contains regex-special characters.
    Why: Avoids 'main' matching 'remained' etc.
    """
    return r'\b' + re.escape(keyword) + r'\b'


def make_snippet(sentence, start, end, context_chars=CONTEXT_CHARS):
    """
    Produce a short snippet around the [start:end] indices inside 'sentence'.
    Adds "..." at beginning or end if snippet is trimmed.
    Why: Quick human-readable preview for the match in the summary list.
    """
    s = max(0, start - context_chars)
    e = min(len(sentence), end + context_chars)
    prefix = "..." if s > 0 else ""
    suffix = "..." if e < len(sentence) else ""
    snippet = prefix + sentence[s:e].strip() + suffix
    return snippet


def highlight_sentence_with_colors(sentence, keywords, kw_color_map, case_sensitive=False):
    """
    Highlight all occurrences of any keyword in 'sentence' using per-keyword colors.
    - Build a grouped regex (kw1|kw2|...) where each keyword is escaped.
    - Replacement function identifies which keyword matched (preserving original text case)
      and wraps it with the color sequence and reset sequence.
    - Returns the highlighted sentence as a string.
    Why: Single-pass replacement keeps original sentence punctuation and spacing intact.
    """
    # Escape every keyword so special characters are literal
    escaped = [re.escape(k) for k in keywords]
    # Group them into a single 'alternation' pattern: (kw1|kw2|kw3)
    group = r'(' + '|'.join(escaped) + r')'
    # Set regex flags: IGNORECASE if not case_sensitive, otherwise 0
    flags = 0 if case_sensitive else re.IGNORECASE

    def repl(m):
        """
        Replacement function called for each regex match:
        - m.group(0) is the matched text as it appears in sentence (preserves case)
        - identify original keyword (by comparing lowercased if case-insensitive)
        - wrap with color and reset sequences
        """
        matched_text = m.group(0)
        matched_kw = None
        # Find which keyword corresponds to the matched text
        for kw in keywords:
            if (matched_text == kw) or (not case_sensitive and matched_text.lower() == kw.lower()):
                matched_kw = kw
                break
        color = kw_color_map.get(matched_kw, "")
        reset = Style.RESET_ALL if Style else ""
        # Preserve original matched text but wrap in color
        return f"{color}{matched_text}{reset}"

    # Perform substitution for all matches in sentence
    highlighted = re.sub(group, repl, sentence, flags=flags)
    return highlighted


def collect_all_matches(folder_path, keywords, case_sensitive=False):
    """
    Walk through all '.txt' files in folder_path, split each file into sentences,
    find all whole-word matches for ANY keyword, and collect Match records.
    Returns a list of Match objects.
    Why:
      - We collect everything first so we can show a preview list, counts, and support navigation.
      - Pre-compiling regex patterns speeds up repeated matching across many sentences.
    """
    # Ensure the folder exists before proceeding — helpful early error for the user.
    if not os.path.isdir(folder_path):
        raise FileNotFoundError(f"Folder not found: {folder_path}")

    matches = []      # list to collect Match records

    # Pre-compile regex patterns per keyword (faster when scanning many sentences)
    patterns = {}
    for kw in keywords:
        # compile pattern with correct flags (case-insensitive unless case_sensitive True)
        patterns[kw] = re.compile(whole_word_pattern(kw), 0 if case_sensitive else re.IGNORECASE)

    # Walk files in sorted order for stable, predictable output across runs
    for fname in sorted(os.listdir(folder_path)):
        # Only consider files ending with .txt (case-insensitive)
        if not fname.endswith(".txt"):
            continue
        file_path = os.path.join(folder_path, fname)
        # Read file content using UTF-8 encoding, skipping files that fail to open
        try:
            with open(file_path, "r", encoding="utf-8") as fh:
                content = fh.read()
        except Exception as e:
            print(f"[ERROR] Could not read '{file_path}': {e}")
            continue

        # Split into sentences by a simple rule: punctuation (.!? ) followed by whitespace
        # This is the same rule used earlier in your project and is good enough for quick previews.
        sentences = re.split(r'(?<=[.!?])\s+', content)

        # For each sentence we check each compiled pattern using finditer to capture positions
        for sentence in sentences:
            for kw, pat in patterns.items():
                for m in pat.finditer(sentence):
                    start, end = m.start(), m.end()
                    snippet = make_snippet(sentence, start, end)
                    matches.append(Match(file=fname, sentence=sentence, start=start, end=end, keyword=kw, snippet=snippet))

    # Return all matched records (could be empty list if no matches)
    return matches


# -----------------------
# Editor opening helpers
# -----------------------

def compute_match_file_line(file_path, sentence, match_start_in_sentence):
    """
    Compute the 1-based line number in the file corresponding to the start of the match.
    Approach:
      - Read full file text.
      - Find the first occurrence of the sentence in the file (we assume the sentence text is unique enough).
      - Compute the absolute character offset where the match occurs:
          file_offset = sentence_offset_in_file + match_start_in_sentence
      - Convert file_offset to line number by counting newlines before that offset.
    Returns (line_number, column) both 1-based, or (None, None) if we can't find the sentence.
    Why:
      - Editors usually accept a line number to jump to; we compute it precisely.
      - Using the sentence search is robust if sentence boundaries are preserved in the file.
    """
    try:
        with open(file_path, "r", encoding="utf-8") as fh:
            full = fh.read()
    except Exception as e:
        # If we can't open the file, return None values (caller will handle fallback)
        print(f"[ERROR] Could not read file to compute line number: {e}")
        return None, None

    # Try to locate the sentence inside the full file text
    # We attempt an exact match; if the sentence is present multiple times, this picks the first.
    idx = full.find(sentence)
    if idx == -1:
        # As a fallback, try a best-effort: search by the snippet (shorter string)
        # This helps if sentence splitting trimmed whitespace differently.
        snippet = sentence.strip()
        idx = full.find(snippet)
        if idx == -1:
            return None, None

    # file_offset is where the sentence starts in the file.
    file_offset = idx + match_start_in_sentence

    # Compute 1-based line number by counting '\n' up to file_offset
    line_number = full.count("\n", 0, file_offset) + 1
    # Compute column by finding the last newline before file_offset
    last_nl = full.rfind("\n", 0, file_offset)
    if last_nl == -1:
        column = file_offset + 1  # no newline before → column is offset+1 (1-based)
    else:
        column = file_offset - last_nl
    return line_number, column


def open_in_pycharm(file_path, line=None, column=None):
    """
    Try to open the given file in PyCharm at the given line (and optional column).
    Strategy:
      1) If 'charm' (PyCharm command-line launcher) is available on PATH, use it.
         Example: charm --line 120 /path/to/file (some versions accept file:line)
      2) If not available, attempt general OS open:
         - On Windows: os.startfile(file_path)
         - On macOS: 'open' command via subprocess
         - On Linux: 'xdg-open' via subprocess
    Notes:
      - PyCharm's CLI 'charm' behavior may vary by version/OS. Users are encouraged to set up 'charm'.
      - If 'charm' isn't present, we still open the file in the system default editor as a fallback.
    Returns True if a command was launched successfully, False otherwise.
    """
    # Normalize path
    file_path = os.path.abspath(file_path)

    # 1) If `charm` exists on PATH, try to use it with line number if supported.
    if which(PYCHARM_LAUNCHER_CMD):
        try:
            # Some 'charm' versions accept 'charm file:line' or 'charm --line line file'
            # We'll try both forms; if first fails, second may work.
            if line:
                # Try "charm file:line" first (common)
                try:
                    subprocess.Popen([PYCHARM_LAUNCHER_CMD, f"{file_path}:{line}"])
                    return True
                except Exception:
                    # Fall back to explicit --line if available
                    try:
                        subprocess.Popen([PYCHARM_LAUNCHER_CMD, "--line", str(line), file_path])
                        return True
                    except Exception:
                        # Give up on charm method
                        pass
            else:
                # No line number requested, just open file
                subprocess.Popen([PYCHARM_LAUNCHER_CMD, file_path])
                return True
        except Exception:
            # If anything fails with charm, we will fall back below
            pass

    # 2) Platform-specific fallback: open file with system default app
    try:
        if sys.platform.startswith("win"):
            # Windows: os.startfile will use the registered app for the file type
            os.startfile(file_path)
            return True
        elif sys.platform == "darwin":
            # macOS: 'open' command
            subprocess.Popen(["open", file_path])
            return True
        else:
            # Assume Linux or similar: use xdg-open
            subprocess.Popen(["xdg-open", file_path])
            return True
    except Exception as e:
        print(f"[ERROR] Could not open file with system opener: {e}")
        return False

# -----------------------
# Interactive navigation UI
# -----------------------

def interactive_navigation(matches, keywords, kw_color_map, case_sensitive=False):
    """
    Presents matches previews and allows interactive navigation.
    Commands:
      - n or Enter: next match
      - p          : previous match
      - number     : jump to that match number (1-based)
      - o          : open current match file in PyCharm (or fallback)
      - q          : quit navigation
    The function prints the highlighted sentence and a snippet for each match.
    """
    # If no matches, inform and return early
    if not matches:
        print("No matches found.")
        return

    # Print a summary list of matches (index + filename + colored snippet)
    print(f"\nFound {len(matches)} matches. Showing previews (context snippets):\n")
    for i, m in enumerate(matches, start=1):
        # Use color highlighting in the preview snippet
        preview = highlight_sentence_with_colors(m.snippet, keywords, kw_color_map, case_sensitive=case_sensitive)
        print(f"{i:04d}. {m.file} - {preview}")

    # Navigation index (0-based)
    idx = 0
    print("\nNavigation commands: 'n' = next, 'p' = previous, a number = jump, 'o' = open in editor, 'q' = quit")

    # Loop until user quits
    while True:
        current = matches[idx]
        # Show full sentence with colors applied
        full_colored = highlight_sentence_with_colors(current.sentence, keywords, kw_color_map, case_sensitive=case_sensitive)
        print("\n" + "="*80)
        print(f"Match {idx+1}/{len(matches)}  —  File: {current.file}  —  Keyword: {current.keyword}")
        print("- Full sentence (highlighted):")
        # print full colored sentence; strip to remove leading/trailing blank lines
        print(full_colored.strip())
        print("- Snippet:")
        print(current.snippet)
        print("="*80)

        # Read command from user
        cmd = input("\nCommand (n/p/number/o/q): ").strip()

        # Quit commands
        if cmd.lower() in ("q", "quit", "exit"):
            print("Exiting navigation.")
            break

        # Next or empty (Enter) -> next match (circular)
        if cmd == "" or cmd.lower() == "n":
            idx = (idx + 1) % len(matches)
            continue

        # Previous -> previous match (circular)
        if cmd.lower() == "p":
            idx = (idx - 1) % len(matches)
            continue

        # Open in editor: compute line and open
        if cmd.lower() == "o":
            # Compute file path relative to CHAPTERS_FOLDER
            file_path = os.path.join(CHAPTERS_FOLDER, current.file)
            # Compute line number in file for match start
            line, col = compute_match_file_line(file_path, current.sentence, current.start)
            if line:
                print(f"Opening {current.file} at line {line} (column {col}) in editor...")
            else:
                print(f"Opening {current.file} in editor (line not found precisely; opening file).")

            ok = open_in_pycharm(file_path, line=line, column=col)
            if not ok:
                print("Failed to open in PyCharm/OS default editor. Check your 'charm' launcher or system opener.")
            # Keep current match displayed (do not change idx)
            continue

        # Try to interpret as a number to jump to
        try:
            num = int(cmd)
            if 1 <= num <= len(matches):
                idx = num - 1
            else:
                print(f"Number out of range. Enter 1..{len(matches)}")
        except ValueError:
            # Unrecognized command
            print("Unknown command. Use 'n', 'p', a number, 'o' to open file, or 'q' to quit.")

# -----------------------
# Main entry point
# -----------------------

def main():
    """
    Main program flow:
      1. Ensure chapters folder exists.
      2. Ask user for comma-separated keywords.
      3. Collect all matches across chapters.
      4. Build color map and enter interactive navigation.
    """
    # 1) Validate chapters folder presence (fail early so user corrects issue).
    if not os.path.isdir(CHAPTERS_FOLDER):
        print(f"[ERROR] chapters folder not found at: {CHAPTERS_FOLDER}")
        print("Place your chapter .txt files in a folder named 'chapters' next to this script.")
        sys.exit(1)

    # 2) Prompt user for keywords (comma-separated)
    raw = input("Enter keyword(s) separated by commas (e.g., 'fog, Klein, ritual'): ").strip()
    if not raw:
        print("No keywords provided. Exiting.")
        return

    # Build a clean list of keywords preserving input order
    keywords = [k.strip() for k in raw.split(",") if k.strip()]

    # 3) Use global case sensitivity flag for the search behavior
    case_sensitive = False  # hard-coded here to keep search forgiving; change to CASE_SENSITIVE_MODE if you prefer

    # 4) Build per-keyword color mapping for consistent coloring
    kw_color_map = build_keyword_color_map(keywords)

    # 5) Collect matches across all chapter files (may take a moment for many files)
    print("Collecting matches across chapter files (this may take a moment)...")
    matches = collect_all_matches(CHAPTERS_FOLDER, keywords, case_sensitive=case_sensitive)

    # 6) Enter interactive navigation UI
    interactive_navigation(matches, keywords, kw_color_map, case_sensitive=case_sensitive)


# Standard Python "entry point" check so script runs only when executed directly
if __name__ == "__main__":
    main()

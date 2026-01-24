# Interactive multi-keyword search with:
#  - distinct colors per keyword
#  - context preview (snippet around the match)
#  - list of matches (file + snippet)
#  - interactive navigation: n (next), p (prev), number (jump), o (open in editor), q (quit)

import os  # for file and path handling, launching OS commands

from .highlight import highlight_sentence_with_colors, CHAPTERS_FOLDER
from .open_in_pycharm import open_in_pycharm, compute_match_file_line


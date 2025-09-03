# =========================
# FUNCTION: highlight_keywords
# =========================
import re

from config import CASE_SENSITIVE_MODE


def highlight_keywords(sentence, keywords):
    """
    Takes a sentence and a list of keywords.
    Returns the sentence with all matching keywords highlighted in **UPPERCASE** and surrounded by **.
    Purpose: Makes it visually clear where matches occurred in the output.
    """
    # Determine regex matching mode based on case sensitivity setting.
    # flags = 0 means default (case-sensitive); re.IGNORECASE means ignore letter case.
    flags = 0 if CASE_SENSITIVE_MODE else re.IGNORECASE

    # Loop through each keyword provided by the user.
    for keyword in keywords:
        # Build a regex pattern that matches the keyword as a "whole word".
        # \b → word boundary (ensures 'main' won't match 'remained').
        # re.escape(keyword) → escapes any regex-special characters in the keyword so they are matched literally.
        pattern = r'\b' + re.escape(keyword) + r'\b'

        # Replace each match with a highlighted version.
        # re.sub → Finds all matches and replaces them.
        # lambda m → For each match object 'm', we take m.group(0) (the exact matched text)
        # and wrap it in ** and convert to uppercase for emphasis.
        sentence = re.sub(pattern, lambda m: f"**{m.group(0)}**", sentence, flags=flags)

    # Return the modified sentence with all highlights applied.
    return sentence

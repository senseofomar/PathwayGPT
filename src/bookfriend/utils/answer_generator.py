import os
import google.generativeai as genai
from dotenv import load_dotenv

# Load environment variables (to get GEMINI_API_KEY)
load_dotenv()


def generate_answer(query, context_chunks, memory=None):
    """
    Generates an answer using Google Gemini (Free Tier).
    Replaces OpenAI to avoid quota issues.
    """
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        return "⚠️ Error: Missing GEMINI_API_KEY in .env file."

    # 1. Configure Gemini
    genai.configure(api_key=api_key)

    # Use 'gemini-1.5-flash' (Fastest & Free-tier eligible)
    model = genai.GenerativeModel('gemini-1.5-flash')

    # 2. Prepare Context from RAG
    context_text = "\n\n".join(context_chunks) if context_chunks else "No relevant excerpts found."

    # 3. Construct Memory String (if provided)
    memory_text = ""
    if memory:
        # Get last 6 messages to keep the conversation flowing
        recent = memory.get_context(limit=6)
        if recent:
            memory_text = "\n\n--- RECENT CONVERSATION ---\n"
            for msg in recent:
                memory_text += f"{msg['role'].upper()}: {msg['content']}\n"

    # 4. Build the Prompt
    # We combine system instructions + memory + context + user question
    prompt = (
        "You are BookFriend, a helpful AI assistant for the novel 'Lord of the Mysteries'.\n"
        "Answer the user's question strictly based on the provided context excerpts below.\n"
        "If the answer isn't in the text, say you don't know. Do not make things up.\n\n"
        f"{memory_text}\n"
        f"--- CONTEXT EXCERPTS ---\n{context_text}\n"
        "------------------------\n\n"
        f"USER QUESTION: {query}\n"
        "ANSWER:"
    )

    # 5. Generate
    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"⚠️ Gemini Error: {str(e)}"
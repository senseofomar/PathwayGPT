# utils/answer_generator.py
import openai

def generate_answer(query, context_chunks, model="gpt-4o-mini"):
    """
    Takes user query + top chunks from semantic search,
    and asks an LLM to summarize or explain the context.
    """
    context_text = "\n\n".join(context_chunks)
    prompt = f"""
You are PathwayGPT, a lore assistant for the web novel 'Lord of the Mysteries'.
Answer based on the following story excerpts (avoid spoilers beyond what is given).

User Query: {query}

Relevant Excerpts:
{context_text}

Your Answer:
"""

    response = openai.ChatCompletion.create(
        model=model,
        messages=[
            {"role": "system", "content": "You are a helpful and spoiler-aware lore assistant."},
            {"role": "user", "content": prompt}
        ]
    )

    return response["choices"][0]["message"]["content"].strip()

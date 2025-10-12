from openai import OpenAI

def generate_answer(query, context_chunks, model="gpt-4o-mini", memory=None):
    """
    Takes user query + top chunks from semantic search,
    and asks an LLM to summarize or explain the context.
    Now supports conversation memory for follow-ups.
    """
    client = OpenAI()

    # Combine context chunks safely
    context_text = "\n\n".join(context_chunks) if context_chunks else "No relevant excerpts found."

    # System-level behavior
    system_prompt = (
        "You are PathwayGPT, a spoiler-aware lore assistant for the web novel 'Lord of the Mysteries'. "
        "Your job is to answer questions strictly using the provided excerpts and recent conversation context. "
        "Avoid adding spoilers, speculation, or knowledge beyond the excerpts. "
        "If something is unclear, admit uncertainty clearly."
    )

    # Base message list
    messages = [{"role": "system", "content": system_prompt}]

    # Add recent conversation memory (last 4 exchanges)
    if memory:
        messages.extend(memory[-4:])

    # Add the new user query and context
    messages.append({
        "role": "user",
        "content": f"User Query: {query}\n\nRelevant Excerpts:\n{context_text}"
    })

    # Call OpenAI API
    response = client.chat.completions.create(
        model=model,
        messages=messages,
        temperature=0.7
    )

    # Extract final answer text
    answer = response.choices[0].message.content.strip()

    return answer

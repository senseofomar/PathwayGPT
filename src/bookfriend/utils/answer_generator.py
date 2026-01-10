from openai import OpenAI

def generate_answer(query, context_chunks, model="gpt-4o-mini", memory=None):
    """
    Generates a lore-aware answer using semantic context and conversation memory.
    - Uses top context chunks from semantic search
    - Integrates last few conversation turns for continuity
    - Avoids spoilers and hallucination beyond provided text
    """
    client = OpenAI()

    # === 1️⃣ Combine context safely ===
    context_text = "\n\n".join(context_chunks) if context_chunks else "No relevant excerpts found."

    # === 2️⃣ Define system behavior ===
    system_prompt = (
        "You are bookfriend, a spoiler-aware lore assistant for the novel 'Lord of the Mysteries'. "
        "Your goal is to answer user questions strictly using the provided excerpts and any recent dialogue context. "
        "If the information is not in the excerpts, politely state that you don’t have enough context. "
        "Avoid spoilers or information beyond what’s explicitly provided."
    )

    # === 3️⃣ Initialize message list ===
    messages = [{"role": "system", "content": system_prompt}]

    # === 4️⃣ Add memory (last few exchanges only, to preserve token limit) ===
    if memory:
        recent_context = memory.get_context(limit=6)  # get last 6 messages (user + assistant)
        if recent_context:
            messages.extend(recent_context)

    # === 5️⃣ Add the new user query and excerpts ===
    user_prompt = (
        f"User Query: {query}\n\n"
        f"Relevant Excerpts:\n{context_text}\n\n"
        "Now answer based strictly on the excerpts above. "
        "If you must infer, do so cautiously and mark it clearly as an interpretation."
    )
    messages.append({"role": "user", "content": user_prompt})

    # === 6️⃣ Call the model ===
    response = client.chat.completions.create(
        model=model,
        messages=messages,
        temperature=0.6,  # lower temp = more accurate factual recall
    )

    # === 7️⃣ Extract and return answer ===
    answer = response.choices[0].message.content.strip()
    return answer

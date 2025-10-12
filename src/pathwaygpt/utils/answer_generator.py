from pathwaygpt.utils.memory_tools import client


def generate_answer(prompt, top_chunks, memory=None):
    context_text = "\n\n".join([chunk['content'] for chunk in top_chunks])
    system_prompt = (
        "You are PathwayGPT, a helpful and spoiler-aware lore assistant for 'Lord of the Mysteries'. "
        "Use only the provided text context to answer. "
        "If uncertain, say so. Never invent spoilers beyond the user's progress."
    )

    messages = [{"role": "system", "content": system_prompt}]

    # Include recent conversation history if available
    if memory:
        messages.extend(memory[-4:])  # last 4 exchanges

    messages.append({"role": "user", "content": f"{prompt}\n\nContext:\n{context_text}"})

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=messages,
        temperature=0.7
    )

    return response.choices[0].message.content.strip()

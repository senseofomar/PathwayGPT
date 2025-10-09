from openai import OpenAI

client = OpenAI()

def summarize_memory(memory_messages: list, model="gpt-4o-mini"):
    """
    Summarizes user + system messages into a brief memory recap.
    """
    if not memory_messages:
        return "No memory data available."

    combined_context = "\n".join(
        [f"{m['role']}: {m['content']}" for m in memory_messages]
    )

    prompt = f"""
You are PathwayGPT's internal memory summarizer.
Summarize the key themes, queries, and insights in a few sentences.

Conversation Log:
{combined_context}

Summary:
"""

    response = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}]
    )

    return response.choices[0].message.content.strip()


def recall_recent_queries(memory_messages: list, limit=5):
    """
    Returns last N user queries only.
    """
    user_msgs = [m["content"] for m in memory_messages if m["role"] == "user"]
    return user_msgs[-limit:] if user_msgs else []

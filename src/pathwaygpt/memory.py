# src/pathwaygpt/memory.py
class ChatMemory:
    def __init__(self, max_messages=10):
        self.history = []
        self.max_messages = max_messages

    def add(self, role, content):
        """Add a message and truncate if needed."""
        self.history.append({"role": role, "content": content})
        if len(self.history) > self.max_messages:
            self.history.pop(0)

    def get_context(self):
        """Return conversation history formatted for the model."""
        return self.history

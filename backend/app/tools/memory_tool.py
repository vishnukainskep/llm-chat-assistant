import logging
from langchain_core.tools import tool

_MEMORY = []

@tool
def add_memory(user_input: str, assistant_output: str) -> str:
    """Add a conversation pair to in-memory store."""
    logging.info("add_memory tool CALLED")
    _MEMORY.append({"user_input": user_input, "assistant_output": assistant_output})
    return "saved"

@tool
def get_recent_conversations(limit: int = 10) -> str:
    """Return recent conversations from in-memory store."""
    logging.info("get_recent_conversations tool CALLED")
    items = _MEMORY[-limit:] if limit and limit > 0 else _MEMORY
    results = []
    for doc in items:
        results.append(
            f"User: {doc.get('user_input')}\n"
            f"Assistant: {doc.get('assistant_output')}\n"
        )
    return "\n---\n".join(results) if results else "No conversations found."

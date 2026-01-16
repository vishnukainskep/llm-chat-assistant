import logging
from langchain_core.tools import tool
from app.db.mongo import mongo_collection

@tool
def get_recent_conversations() -> str:
    """Fetch recent conversations from MongoDB."""
    logging.info("get_recent_conversations tool CALLED")

    docs = mongo_collection.find()
    results = []

    for doc in docs:
        results.append(
            f"User: {doc.get('user_input')}\n"
            f"Assistant: {doc.get('assistant_output')}\n"
        )

    return "\n---\n".join(results) if results else "No conversations found."

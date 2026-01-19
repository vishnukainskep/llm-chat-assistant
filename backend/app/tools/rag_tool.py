from langchain_core.tools import Tool
from pathlib import Path
import logging
from app.vector.vectorstore import get_vectorstore

logger = logging.getLogger(__name__)

DOCS_PATH = Path(__file__).parent.parent / "vector" / "docs.txt"
METHODS = ["GET", "POST", "PUT", "DELETE", "PATCH"]

def rag_search_impl(query: str, k: int = 3) -> str:
    content = ""

    try:
        vs = get_vectorstore()
        docs = vs.similarity_search(query, k=k)
        if docs:
            content = "\n".join(d.page_content for d in docs)
    except Exception as e:
        logger.warning(f"Vectorstore failed: {e}")

    if not content:
        if not DOCS_PATH.exists():
            return "No API documentation found."

        content = DOCS_PATH.read_text(encoding="utf-8")

    base_url = ""
    method = ""
    endpoint = ""

    for line in content.splitlines():
        text = line.strip()
        low = text.lower()
        up = text.upper()

        if low.startswith("base url:"):
            base_url = text.split(":", 1)[1].strip()

        if low.startswith("endpoint:"):
            endpoint = text.split(":", 1)[1].strip()

        for m in METHODS:
            if m in up:
                method = m

        if not endpoint and "/" in text and any(m in up for m in METHODS):
            endpoint = text[text.find("/"):].split()[0]

    result = "API Documentation Found:\n\n" + content + "\n\n"

    if endpoint:
        result += (
            "Extracted API Details:\n"
            f"Method: {method}\n"
            f"Endpoint: {endpoint}\n"
            f"Base URL: {base_url}\n"
            f"Full URL: {base_url}{endpoint}\n"
        )

    return result


rag_search = Tool(
    name="rag_search",
    description="Search API docs and return method + URL",
    func=rag_search_impl,
)

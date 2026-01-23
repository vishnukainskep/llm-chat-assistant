from langchain_core.tools import Tool
from pathlib import Path
import logging
from app.vector.vectorstore import get_vectorstore

logger = logging.getLogger(__name__)

DOCS_PATH = Path(__file__).parent.parent / "vector" / "docs.txt"
HTTP_METHODS = ["GET", "POST", "PUT", "DELETE", "PATCH"]


def rag_search_impl(query: str, k: int = 3) -> str:
    """
    Search API documentation using vector search.
    Falls back to docs.txt if vector search fails.
    """

    docs_text = ""

    # ------------------ vector search ------------------ 
    try:
        vectorstore = get_vectorstore()
        docs = vectorstore.similarity_search(query, k=k)
        if docs:
            docs_text = "\n".join(doc.page_content for doc in docs)
    except Exception as e:
        logger.warning(f"Vector search failed: {e}")

    if not docs_text:
        if not DOCS_PATH.exists():
            return "No API documentation found."
        docs_text = DOCS_PATH.read_text(encoding="utf-8")

    # ------------------  Extract simple API details ------------------ 
    base_url = ""
    method = ""
    endpoint = ""

    for line in docs_text.splitlines():
        line = line.strip()

        if line.lower().startswith("base url:"):
            base_url = line.split(":", 1)[1].strip()

        if line.lower().startswith("endpoint:"):
            endpoint = line.split(":", 1)[1].strip()

        for http_method in HTTP_METHODS:
            if http_method in line.upper():
                method = http_method

    # ---------------- Build response ------------------ 
    result = f"API Documentation:\n\n{docs_text}\n"

    if endpoint:
        result += (
            "\nExtracted API Details:\n"
            f"Method: {method}\n"
            f"Endpoint: {endpoint}\n"
            f"Base URL: {base_url}\n"
            f"Full URL: {base_url}{endpoint}\n"
        )

    return result


rag_search = Tool(
    name="rag_search",
    description="Search API documentation and extract endpoint details",
    func=rag_search_impl,
)

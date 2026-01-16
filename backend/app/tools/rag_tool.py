# from langchain_core.tools import Tool
# from pathlib import Path
# import logging
# from app.vector.vectorstore import get_vectorstore

# logger = logging.getLogger(__name__)

# DOCS_PATH = Path(__file__).parent.parent / "vector" / "docs.txt"

# def format_api_info(content: str) -> str:
#     base_url = "https://fakestoreapi.com"
#     method = "GET"
#     endpoint = ""
#     for line in content.splitlines():
#         line_stripped = line.strip()
#         lower = line_stripped.lower()
#         if lower.startswith("base url:"):
#             parts = line_stripped.split(":", 1)
#             if len(parts) == 2:
#                 value = parts[1].strip()
#                 if value:
#                     base_url = value
#         upper = line_stripped.upper()
#         for m in ["GET", "POST", "PUT", "DELETE", "PATCH"]:
#             if m in upper:
#                 method = m
#                 break
#         if lower.startswith("endpoint:") and not endpoint:
#             parts = line_stripped.split(":", 1)
#             if len(parts) == 2:
#                 value = parts[1].strip()
#                 if value:
#                     endpoint = value
#     if not endpoint:
#         for line in content.splitlines():
#             upper = line.upper()
#             for m in ["GET", "POST", "PUT", "DELETE", "PATCH"]:
#                 token = m + " "
#                 if token in upper:
#                     idx = upper.find("/")
#                     if idx != -1:
#                         original = line[idx:].strip()
#                         endpoint = original.split()[0]
#                         break
#             if endpoint:
#                 break
#     formatted = "API Documentation Found:\n" + content + "\n\n"
#     if endpoint:
#         full_url = base_url + endpoint
#         formatted += "--- EXTRACTED API DETAILS ---\n"
#         formatted += "Method: " + method + "\n"
#         formatted += "Endpoint: " + endpoint + "\n"
#         formatted += "Base URL: " + base_url + "\n"
#         formatted += "Full URL: " + full_url + "\n"
#         formatted += "--- USE THESE DETAILS WITH api_agent ---\n"
#     return formatted

# def simple_rag_search(query: str, k: int = 3) -> str:
#     try:
#         if not DOCS_PATH.exists():
#             return "No API documentation found."
#         with open(DOCS_PATH, "r", encoding="utf-8") as f:
#             content = f.read()
#         sections = []
#         current = []
#         for line in content.splitlines():
#             if line.strip().startswith("=" * 10):
#                 if current:
#                     sections.append("\n".join(current))
#                     current = []
#             else:
#                 current.append(line)
#         if current:
#             sections.append("\n".join(current))
#         query_lower = query.lower()
#         keywords = query_lower.split()
#         matches = []
#         for section in sections:
#             section_lower = section.lower()
#             score = 0
#             for word in keywords:
#                 if word in section_lower:
#                     score += 1
#             if score > 0:
#                 matches.append((score, section.strip()))
#         matches.sort(reverse=True, key=lambda x: x[0])
#         top_matches = [m[1] for m in matches[:k]]
#         if not top_matches:
#             return "No relevant API info found."
#         result = "\n\n".join(top_matches)
#         return format_api_info(result)
#     except Exception as e:
#         logger.error(f"Simple RAG search failed: {e}")
#         return "RAG error: " + str(e)

# def rag_search_impl(query: str, k: int = 3) -> str:
#     try:
#         vectorstore = None
#         try:
#             vectorstore = get_vectorstore()
#         except Exception as e:
#             logger.warning(f"Vectorstore unavailable, using simple RAG: {e}")
#         if vectorstore:
#             docs = vectorstore.similarity_search(query, k=k)
#             if docs:
#                 content = ""
#                 for doc in docs:
#                     content += doc.page_content + "\n"
#                 return format_api_info(content)
#             return simple_rag_search(query, k)
#         return simple_rag_search(query, k)
#     except Exception as e:
#         logger.error(f"RAG search failed: {e}")
#         return simple_rag_search(query, k)

# rag_search = Tool(
#     name="rag_search",
#     description=(
#         "Search API documentation from docs.txt. "
#         "Returns method, endpoint, and full URL for API-related queries. "
#         "Input: Any question or query."
#     ),
#     func=rag_search_impl
# )


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

    base_url = "https://fakestoreapi.com"
    method = "GET"
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

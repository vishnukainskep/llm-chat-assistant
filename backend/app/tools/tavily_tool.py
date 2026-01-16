import os
import logging
from tavily import TavilyClient
from langchain_core.tools import tool

tavily_client = TavilyClient(api_key=os.getenv("TAVILY_API_KEY"))

@tool
def tavily_search(query: str) -> str:
    """
    Search the web using Tavily.
    Use this for current information, real-time data, or factual lookup.
   """
    logging.info("🔍 tavily_search tool CALLED")

    response = tavily_client.search(
        query=query,
        search_depth="basic",
        max_results=5
    )

    results = []
    for item in response.get("results", []):
        results.append(
            f"Title: {item['title']}\n"
            f"URL: {item['url']}\n"
            f"Content: {item['content']}\n"
        )

    return "\n\n".join(results) if results else "No results found."

import json
import logging
import requests
from langchain_core.tools import tool

@tool
def api_agent(endpoint: str | dict, params: dict = {}) -> str:
    """
    Calls an external API and returns the response.
    Accepts either:
    - endpoint as string
    - OR endpoint wrapped in a dict 
    """
    logging.info("api_agent tool CALLED")

    try:
        if isinstance(endpoint, dict):
            params = endpoint.get("params", {})
            endpoint = endpoint.get("endpoint")

        if isinstance(endpoint, str) and endpoint.strip().startswith("{"):
            payload = json.loads(endpoint)
            endpoint = payload.get("endpoint")
            params = payload.get("params", {})

        response = requests.get(endpoint, params=params, timeout=10)
        response.raise_for_status()
        return response.text

    except Exception as e:
        logging.error(f"API call failed: {e}")
        return f"API call failed: {e}"

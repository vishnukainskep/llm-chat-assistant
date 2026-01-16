import logging
import requests
from langchain_core.tools import tool
from datetime import datetime

@tool
def joke_generator(message: str = "") -> str:
    """Fetch a random joke from the official joke API"""
    logging.info("joke_generator tool CALLED")
    response = requests.get(
        "https://official-joke-api.appspot.com/random_joke", timeout=10
    )
    data = response.json()
    return f"{data['setup']} ... {data['punchline']}"

@tool
def current_time(message: str = "") -> str:
    """Return the current time and date in proper format."""
    logging.info("current_time tool CALLED")
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

@tool
def solve_math(expression: str) -> str:
    """Solve a mathematical expression safely."""
    allowed_chars = "0123456789+-*/(). "
    if any(c not in allowed_chars for c in expression):
        return "Invalid characters in expression."
    return str(eval(expression))

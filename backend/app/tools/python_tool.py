import logging
from langchain_core.prompts import PromptTemplate
from langchain_core.tools import tool
from app.core.llm import llm

@tool
def python_expert(user_input: str) -> str:
    """Provides Python expertise, debugging, and best practices."""
    logging.info("🐍 python_expert tool CALLED")

    prompt = PromptTemplate.from_template(
        """
You are a Python expert assistant.
You ONLY answer Python-related questions.

Rules:
- Explain clearly
- Fix bugs if code is given
- If NOT Python-related, reply:
  'I can only help with Python-related questions.'

User input:
{user_input}
"""
    )

    response = llm.invoke(prompt.format(user_input=user_input))
    return response.content

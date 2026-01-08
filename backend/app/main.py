from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv

import os
import asyncio
import logging

from tavily import TavilyClient
from langchain_openai import AzureChatOpenAI
from langchain_core.prompts import PromptTemplate
from langchain_core.tools import tool
from langchain.agents.agent import AgentExecutor
from langchain.agents.react.agent import create_react_agent

load_dotenv()
logging.basicConfig(level=logging.INFO)

app = FastAPI(title="Gemini FastAPI")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5174",
        "http://localhost:5173",
        "http://127.0.0.1:5174",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

llm = AzureChatOpenAI(
    api_key=os.getenv("AZURE_OPENAI_API_KEY"),
    azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
    azure_deployment=os.getenv("AZURE_OPENAI_MODEL"),
    api_version=os.getenv("AZURE_OPENAI_API_VERSION"),
    temperature=0.2,
)

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

tavily_client = TavilyClient(
    api_key=os.getenv("TAVILY_API_KEY")
)

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

import requests

@tool
def api_agent(endpoint: str, params: dict = {}) -> str:
    """
    Calls an external API and returns the response.
    Use for structured data lookup from public APIs.
    """
    logging.info("🌐 api_agent tool CALLED")
    try:
        response = requests.get(endpoint, params=params, timeout=10)
        response.raise_for_status()
        return response.text 
    except Exception as e:
        logging.error(f"API call failed: {e}")
        return f"API call failed: {e}"

@tool
def joke_generator(message: str = "") -> str:
    """Fetch a random joke from the official joke API"""
    logging.info("😂 joke_generator tool CALLED")
    try:
        response = requests.get(
            "https://official-joke-api.appspot.com/random_joke", timeout=10
        )
        response.raise_for_status()
        data = response.json()
        return f"{data['setup']} ... {data['punchline']}"
    except Exception as e:
        logging.error(f"Failed to get joke: {e}")
        return f"Failed to fetch a joke: {e}"

@tool
def current_time(message: str = "") -> str:
    """Return the current time and date in proper format."""
    logging.info("⏰ current_time tool CALLED")
    from datetime import datetime
    now = datetime.now()
    return now.strftime("%Y-%m-%d %H:%M:%S")

@tool
def solve_math(expression: str) -> str:
    """Solve a mathematical expression safely."""
    try:
        allowed_chars = "0123456789+-*/(). "
        if any(c not in allowed_chars for c in expression):
            return "Invalid characters in expression."
        result = eval(expression)
        return str(result)
    except Exception as e:
        return f"Math evaluation failed: {e}"


prompt = PromptTemplate.from_template(
    """
You are a ReAct agent.

You have access to the following tools:
{tools}

Tool names:
{tool_names}

Rules:
- For Python questions → use python_expert
- For real-time, factual, or web search questions → use tavily_search
- For current time/date → use current_time
- For API or structured data requests → use api_agent
- For math problems → use solve_math
- For jokes → use joke_generator
- For greetings / testing → use agent_heartbeat
- NEVER answer directly without a tool

Use this format:

Question: {input}
Thought: reason about what to do
Action: the tool to use, one of [{tool_names}]
Action Input: input to the tool
Observation: tool result
... (repeat if needed)
Thought: I now know the final answer
Final Answer: answer to the user

Begin!

Question: {input}
{agent_scratchpad}
"""
)

# -------------------------------------------------
# Create Agent + Executor
# -------------------------------------------------
tools = [python_expert, tavily_search, api_agent, joke_generator, current_time, solve_math]

agent = create_react_agent(
    llm=llm,
    tools=tools,
    prompt=prompt,
)

agent_executor = AgentExecutor(
    agent=agent,
    tools=tools,
    verbose=True,
)

class QueryRequest(BaseModel):
    user_input: str

@app.post("/ask/stream")
async def ask_llm_stream(request: QueryRequest):
    try:
        result = agent_executor.invoke({"input": request.user_input})

        async def token_generator():
            yield result["output"]
            await asyncio.sleep(0)

        return StreamingResponse(token_generator(), media_type="text/plain")

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

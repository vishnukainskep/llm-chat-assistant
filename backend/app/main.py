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

# -------------------------------------------------
# Basic setup
# -------------------------------------------------
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

# -------------------------------------------------
# LLM (Azure OpenAI) — FIXED
# -------------------------------------------------
llm = AzureChatOpenAI(
    api_key=os.getenv("AZURE_OPENAI_API_KEY"),
    azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
    azure_deployment=os.getenv("AZURE_OPENAI_MODEL"),
    api_version=os.getenv("AZURE_OPENAI_API_VERSION"),
    temperature=0.2,
)

# -------------------------------------------------
# TOOL 1: Python Expert
# -------------------------------------------------
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

# -------------------------------------------------
# TOOL 2: Agent Heartbeat (DEBUG TOOL)
# -------------------------------------------------
@tool
def agent_heartbeat(message: str) -> str:
    """Confirms agent execution."""
    logging.info("💓 agent_heartbeat tool CALLED")
    return "🟢 AGENT TOOL INVOKED — this is NOT a plain LLM response"

# -------------------------------------------------
# TOOL 3: Tavily Search (WEB SEARCH)
# -------------------------------------------------
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

# -------------------------------------------------
# ReAct PROMPT (THIS IS THE CRITICAL FIX)
# -------------------------------------------------
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
tools = [python_expert, agent_heartbeat, tavily_search]

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

# -------------------------------------------------
# API schema
# -------------------------------------------------
class QueryRequest(BaseModel):
    user_input: str

# -------------------------------------------------
# API endpoint
# -------------------------------------------------
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

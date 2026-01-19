from app.core.llm import llm
from app.tools.python_tool import python_expert
from app.tools.rag_tool import rag_search
from app.tools.api_tool import api_agent
from app.tools.misc_tools import joke_generator, current_time, solve_math
from langchain_classic.memory import ConversationSummaryMemory
import json

# Initialize memory with the LLM for summarization
agent_memory = ConversationSummaryMemory(llm=llm, memory_key="chat_summary")

tools = [
    rag_search,
    api_agent,
    python_expert,
    joke_generator,
    current_time,
    solve_math,
]

tool_map = {tool.name: tool for tool in tools}

BASE_PROMPT = """
You are a technical assistant capable of searching documentation and executing API calls.
CRITICAL RULE: You MUST NOT guess API endpoints or base URLs. Always use 'rag_search' first to find the correct API details from the documentation.

Tools available:
{tools}

Conversation Summary:
{chat_summary}

Mandatory Flow:
1. If the user asks to perform an action (e.g., "show posts", "create user"), ALWAYS call 'rag_search' with a relevant query to find the API endpoint.
2. After receiving API details (Method, URL) from 'rag_search', call 'api_agent' with the correct JSON input.
3. Provide the final result to the user using 'Final Answer:'.

Format:
Thought: ...
Action: <tool name>
Action Input: <valid JSON>
Observation: <result>
Final Answer: <answer>
"""

def build_prompt(question: str, scratchpad: str) -> str:
    tool_names = ", ".join(tool_map.keys())
    memory_vars = agent_memory.load_memory_variables({})
    chat_summary = memory_vars.get("chat_summary", "")
    print(chat_summary)
    
    return (
        BASE_PROMPT.format(tools=tool_names, chat_summary=chat_summary)
        + f"\nHuman: {question}\n"
        + scratchpad
    )

def parse_llm_output(text: str):
    data = {"thought": "", "action": "", "input": ""}

    for line in text.splitlines():
        line = line.strip()
        if line.startswith("Thought:"):
            data["thought"] = line.replace("Thought:", "").strip()
        elif line.startswith("Action:"):
            data["action"] = line.replace("Action:", "").strip()
        elif line.startswith("Action Input:"):
            data["input"] = line.replace("Action Input:", "").strip()

    return data

def run_agent(inputs, verbose=True, max_iterations=15):
    question = inputs["input"]
    scratchpad = ""

    for _ in range(max_iterations):
        prompt = build_prompt(question, scratchpad)
        llm_output = llm.invoke(prompt).content

        if verbose:
            print("\nLLM Output:\n", llm_output)

        if "Final Answer:" in llm_output:
            final_answer = llm_output.split("Final Answer:")[-1].strip()
            agent_memory.save_context({"human_input": question}, {"output": final_answer})
            return {"output": final_answer}

        parsed = parse_llm_output(llm_output)
        tool_name = parsed["action"]
        tool_input = parsed["input"]

        if tool_name not in tool_map:
            scratchpad += f"\nError {tool_name}\n"
            continue

        try:
            tool_input = json.loads(tool_input)
        except json.JSONDecodeError:
            pass

        if verbose:
            print(f"\nCalling Tool: {tool_name}")
            print(f"Tool Input: {tool_input}")

        observation = tool_map[tool_name].invoke(tool_input)

        if verbose:
            print("Observation:", observation)

        scratchpad += f"""
Thought: {parsed['thought']}
Action: {tool_name}
Action Input: {tool_input}
Observation: {observation}
"""
    final_prompt = (
        "You've tried multiple times. Provide a final answer:\n"
        + scratchpad
        + "\nFinal Answer:"
    )

    final_res = llm.invoke(final_prompt).content
    agent_memory.save_context({"human_input": question}, {"output": final_res})
    return {"output": final_res}

agent_executor = run_agent

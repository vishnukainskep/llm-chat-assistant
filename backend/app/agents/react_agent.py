from app.core.llm import llm
from app.tools.python_tool import python_expert
from app.tools.rag_tool import rag_search
from app.tools.api_tool import api_agent
from app.tools.misc_tools import joke_generator, current_time, solve_math
import json

# ------------------ Tools ------------------

tools = [
    rag_search,
    api_agent,
    python_expert,
    joke_generator,
    current_time,
    solve_math,
]

tool_map = {tool.name: tool for tool in tools}

# ------------------ Prompt ------------------

BASE_PROMPT = """
You can use tools to answer questions.
Tools: {tools}

Flow:
1) Use rag_search to find API details.
2) Then call api_agent with method and full URL.
3) Show the final answer to the user.

Format:
Thought: ...
Action: <tool name>
Action Input: <valid JSON>
Observation: <result>
Final Answer: <answer>
"""

def build_prompt(question: str, scratchpad: str) -> str:
    tool_names = ", ".join(tool_map.keys())
    return (
        BASE_PROMPT.format(tools=tool_names)
        + f"\nQuestion: {question}\n"
        + scratchpad
    )

# ------------------ Helpers ------------------

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

# ------------------ Agent ------------------

def run_agent(inputs, verbose=True, max_iterations=15):
    question = inputs["input"]
    scratchpad = ""

    for _ in range(max_iterations):
        prompt = build_prompt(question, scratchpad)
        llm_output = llm.invoke(prompt).content

        if verbose:
            print("\nLLM Output:\n", llm_output)

        if "Final Answer:" in llm_output:
            return {"output": llm_output.split("Final Answer:")[-1].strip()}

        parsed = parse_llm_output(llm_output)
        tool_name = parsed["action"]
        tool_input = parsed["input"]

        if tool_name not in tool_map:
            scratchpad += f"\nError: Unknown tool {tool_name}\n"
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

    # fallback if max iterations reached
    final_prompt = (
        "You've tried multiple times. Provide a final answer:\n"
        + scratchpad
        + "\nFinal Answer:"
    )

    return {"output": llm.invoke(final_prompt).content}

# alias
agent_executor = run_agent

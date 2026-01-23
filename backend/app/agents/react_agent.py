from app.core.llm import llm
from app.tools.python_tool import python_expert
from app.tools.rag_tool import rag_search
from app.tools.api_tool import api_agent
from app.tools.misc_tools import joke_generator, current_time, solve_math
from app.helper.memory_function import MemoryFunction
from app.helper.guardrails import input_guardrail_check, output_guardrail_check

from langchain.tools import tool
import json


@tool
def save_user_profile(info: dict) -> str:
    """Save important user information"""
    return f"Saved user info: {info}"


TOOLS = {
    "rag_search": rag_search,
    "api_agent": api_agent,
    "python_expert": python_expert,
    "joke_generator": joke_generator,
    "current_time": current_time,
    "solve_math": solve_math,
    "save_user_profile": save_user_profile,
}


BASE_PROMPT = """
You are a powerful technical assistant that solves user requests by reasoning step-by-step and using the provided tools.

CRITICAL RULES:
1. NEVER hallucinate or make up data. If you need information from an API, you MUST use 'rag_search' to find the endpoint and 'api_agent' to fetch the data.
2. If the user asks for data (like comments, posts, etc.), you MUST NOT generate a fake list. You MUST call the API.
3. Always check 'rag_search' first if you are unsure of the API endpoint or parameters.
4. If you receive a tool error, try to fix your input or use a different tool.
5. If the user shares personal info (name, phone, etc.), use 'save_user_profile' to store it.

Format:
Thought: your reasoning about what to do next.
Action: the tool name to use (one of: {tools}) OR NONE.
Action Input: the input for the tool (JSON or plain text).
Observation: the result from the tool (this will be provided to you).
... (repeat Thought/Action/Action Input/Observation if needed)
Final Answer: your final response to the user based on tool observations.

Available tools:
{tools_desc}
"""


def run_agent(inputs, max_steps=10, verbose=True):
    question = inputs["input"]
    session_id = inputs.get("session_id", "default")
    user_id = inputs.get("user_id", "default_user")

    # Guardrail Check
    sanitized_question, input_valid, input_risk = input_guardrail_check(question)
    if not input_valid:
        return {"output": "I can’t help with harmful content.", "session_id": session_id}
    question = sanitized_question

    memory = MemoryFunction(session_id, user_id)
    history = memory.get_full_context()

    scratchpad = ""

    tools_desc = "\n".join([f"- {name}: {tool.description}" for name, tool in TOOLS.items()])
    tools_list = ", ".join(TOOLS.keys())

    for step in range(max_steps):
        prompt = f"""
{BASE_PROMPT.format(tools=tools_list, tools_desc=tools_desc)}

Chat History:
{history}

User Question:
{question}

{scratchpad}
"""

        try:
            response = llm.invoke(prompt)
            output = response.content.strip()
        except Exception as e:
            if "content_filter" in str(e).lower():
                return {
                    "output": "I encountered a content filter error. This usually happens when processing sensitive data like phone numbers. I've noted your information and will proceed carefully.",
                    "session_id": session_id
                }
            raise e

        if verbose:
            print(f"\n-------- Agent working --------\n{output}")

        if "Final Answer:" in output:
            final_answer = output.split("Final Answer:")[-1].strip()
            
            if ("comment" in question.lower() or "post" in question.lower()) and "Observation:" not in scratchpad:
                scratchpad += "\nThought: I should have used a tool to fetch real data instead of just providing a final answer. I will now use rag_search to find the correct API endpoint.\n"
                continue

            # Guardrail Check
            sanitized_answer, output_valid, output_risk = output_guardrail_check(question, final_answer)
            final_answer = sanitized_answer if output_valid else "I can’t help with harmful content."

            memory.add_message("user", question)
            memory.add_message("assistant", final_answer)
            return {"output": final_answer, "session_id": session_id}

        lines = {k: "" for k in ["Thought", "Action", "Action Input"]}
        current_key = None
        for line in output.splitlines():
            line = line.strip()
            for key in lines:
                if line.startswith(f"{key}:"):
                    lines[key] = line.replace(f"{key}:", "").strip()
                    current_key = key
                    break
            else:
                if current_key:
                    lines[current_key] += " " + line

        action = lines["Action"]
        action_input = lines["Action Input"]

        if action == "NONE" or not action:
            scratchpad += f"\n{output}\nObservation: No action taken. If you need data, please use a tool.\n"
            continue

        if action not in TOOLS:
            scratchpad += f"\n{output}\nObservation: Unknown tool '{action}'. Please use one of: {tools_list}\n"
            continue

        try:
            if action == "save_user_profile":
                try:
                    info = json.loads(action_input) if isinstance(action_input, str) and (action_input.startswith("{") or action_input.startswith("[")) else {"info": action_input}
                except:
                    info = {"info": action_input}
                memory.update_profile(info)
                result = f"Successfully saved user info: {info}"
            else:
                try:
                    if action == "api_agent" and isinstance(action_input, str) and not action_input.startswith("{"):
                        actual_input = {"endpoint": action_input}
                    else:
                        actual_input = json.loads(action_input)
                except:
                    actual_input = action_input
                
                result = TOOLS[action].run(actual_input)

            scratchpad += f"\nThought: {lines['Thought']}\nAction: {action}\nAction Input: {action_input}\nObservation: {result}\n"
        except Exception as e:
            scratchpad += f"\nThought: {lines['Thought']}\nAction: {action}\nAction Input: {action_input}\nObservation: Tool error - {str(e)}\n"

    return {
        "output": "I'm sorry, I couldn't complete the task within the maximum number of steps. Please try again or rephrase your request.",
        "session_id": session_id,
    }


agent_executor = run_agent

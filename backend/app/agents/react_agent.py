from app.core.llm import llm
from app.tools.python_tool import python_expert
from app.tools.rag_tool import rag_search
from app.tools.api_tool import api_agent
from app.tools.misc_tools import joke_generator, current_time, solve_math
# from langchain_classic.memory import ConversationSummaryMemory
from app.helper.memory_function import MemoryFunction
import json
import re

from langchain.tools import tool

@tool
def save_user_profile(info_json: str) -> str:
    """Useful for saving important user information like name, address, preferences, etc. 
    Input should be a valid JSON string of key-value pairs."""
    try:
        # We'll use a placeholder for memory_func which is available in run_agent scope
        # But for the tool to work, we'll need to pass it or use a global-ish pattern
        # Since tools are usually static, we'll handle this in the run_agent loop for simplicity
        return f"STUB: Saving {info_json}"
    except Exception as e:
        return f"Error: {str(e)}"

tools = [
    rag_search,
    api_agent,
    python_expert,
    joke_generator,
    current_time,
    solve_math,
    save_user_profile
]

tool_map = {tool.name: tool for tool in tools}

BASE_PROMPT = """
You are a helpful and polite technical assistant. You have access to tools and memory to help you provide better answers.

Tools:
{tools}

History and Profile:
{chat_history}

Guidance:
- If the user shares personal details (like their name, contact info, or preferences), use 'save_user_profile' to remember them for future chats.
- Use 'rag_search' to look up technical documentation when needed.
- Use 'api_agent' for any external data requests or actions.
- Keep your tone collaborative.

Response Format:
Thought: [describe your next step]
Action: [the tool to use]
Action Input: [JSON for the tool]
Observation: [result from the tool]
... (continue if more steps are needed)
Final Answer: [your clear and direct response to the user]
"""

def build_prompt(question: str, chat_history: str, scratchpad: str) -> str:
    tool_names = ", ".join(tool_map.keys())
    
    return (
        BASE_PROMPT.format(tools=tool_names, chat_history=chat_history)
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
    session_id = inputs.get("session_id", "default")
    user_id = inputs.get("user_id", "default_user")

    memory_func = MemoryFunction(session_id, user_id)
    chat_history = memory_func.get_full_context()
    
    scratchpad = ""

    for _ in range(max_iterations):
        try:
            prompt = build_prompt(question, chat_history, scratchpad)
            response = llm.invoke(prompt)
            llm_output = response.content
        except Exception as e:
            if "content_filter" in str(e).lower():
                return {
                    "output": "I'm sorry, I encountered a content filter while processing your request. This often happens if personal data like phone numbers are included. I will try to save your information separately next time.", 
                    "session_id": session_id
                }
            raise e

        if verbose:
            print("\nLLM Output:\n", llm_output)

        parsed = parse_llm_output(llm_output)
        tool_name = parsed["action"]
        tool_input = parsed["input"]

        # Process tool if present, even if "Final Answer" is also present
        if tool_name and tool_name in tool_map:
            try:
                # Handle potential string or dict input
                if isinstance(tool_input, str):
                    try:
                        actual_input = json.loads(tool_input)
                    except:
                        actual_input = tool_input
                else:
                    actual_input = tool_input
                    
                if tool_name == "save_user_profile":
                    if isinstance(actual_input, str):
                        try:
                            info = json.loads(actual_input)
                        except:
                            info = {"info": actual_input}
                    else:
                        info = actual_input
                    memory_func.update_profile(info)
                    observation = f"Successfully saved to user profile: {info}"
                else:
                    observation = tool_map[tool_name].run(actual_input)
                
                scratchpad += f"\nObservation: {observation}\n"
                
                # If we processed a tool, we continue to the next iteration to let the LLM see the observation
                # even if it also provided a Final Answer (we want it to confirm it saw the observation)
                continue
            except Exception as e:
                scratchpad += f"\nObservation: Error running tool: {str(e)}\n"
                continue

        # If no tool was called, check for Final Answer
        if "Final Answer:" in llm_output:
            final_answer = llm_output.split("Final Answer:")[-1].strip()
            
            memory_func.add_message("user", question)
            memory_func.add_message("assistant", final_answer)
            
            return {"output": final_answer, "session_id": session_id}

        if not tool_name:
            # Check if there is a Final Answer even if parsing failed
            if "Final Answer:" in llm_output:
                final_answer = llm_output.split("Final Answer:")[-1].strip()
                memory_func.add_message("user", question)
                memory_func.add_message("assistant", final_answer)
                return {"output": final_answer, "session_id": session_id}
            
            scratchpad += f"\nObservation: No action or final answer provided. Please follow the format: Thought, Action, Action Input, or provide a Final Answer.\n"
            continue

    return {"output": "I couldn't find a final answer in time.", "session_id": session_id}

agent_executor = run_agent

from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from langchain_openai import AzureChatOpenAI
from langchain_core.prompts import PromptTemplate
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import os
import asyncio

load_dotenv()

app = FastAPI(title="Gemini FastAPI")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5174",
        "http://127.0.0.1:5174",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

llm = AzureChatOpenAI(
    api_key=os.environ["AZURE_OPENAI_API_KEY"],
    azure_endpoint=os.environ["AZURE_OPENAI_ENDPOINT"],
    model=os.environ["AZURE_OPENAI_MODEL"],
    api_version=os.environ["AZURE_OPENAI_API_VERSION"],
    temperature=0.2,
)

prompt_template = PromptTemplate(
    template=(
        "You are a Python expert assistant.\n"
        "You ONLY help with Python programming.\n\n"

        "Allowed:\n"
        "- Greetings like: hi, hello, hey\n"
        "- All technology of Python \n"
        "- Python questions\n"
        "- Python code debugging\n\n"

        "Rules:\n"
        "- If the user greets you, reply politely and ask for a Python question\n"
        "- If the question is NOT related to Python, reply:\n"
        "  'I can only help with Python-related questions.'\n"
        "- If Python code is provided:\n"
        "  1. Identify errors\n"
        "  2. Explain clearly\n"
        "  3. Fix the code\n"
        "  4. Suggest best practices\n"
        "- Keep answers simple\n\n"

        "User input:\n{user_input}"
    ),
    input_variables=["user_input"],
)

class QueryRequest(BaseModel):
    user_input: str

@app.post("/ask")
async def ask_llm(request: QueryRequest):
    try:
        formatted_prompt = prompt_template.format(
            user_input=request.user_input
        )
        response = llm.invoke(formatted_prompt)
        return {"response": response.content}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# # -------------------------
# # STREAMING ENDPOINT
# # -------------------------
# @app.post("/ask/stream")
# async def ask_llm_stream(request: QueryRequest):
#     try:
#         formatted_prompt = prompt_template.format(
#             user_input=request.user_input
#         )

#         async def token_generator():
#             # LangChain streaming
#             for chunk in llm.stream(formatted_prompt):
#                 if chunk.content:
#                     yield chunk.content
#                 await asyncio.sleep(0)  # allow event loop to breathe

#         return StreamingResponse(
#             token_generator(),
#             media_type="text/plain"
#         )

#     except Exception as e:
#         raise HTTPException(status_code=500, detail=str(e))
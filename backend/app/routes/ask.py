import asyncio
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from app.schema.request import QueryRequest
from app.agents.react_agent import agent_executor

router = APIRouter()

@router.post("/ask/stream")
async def ask_llm_stream(request: QueryRequest):
    try:
        result = agent_executor({"input": request.user_input})

        async def token_generator():
            yield result["output"]
            await asyncio.sleep(0)

        return StreamingResponse(token_generator(), media_type="text/plain")

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

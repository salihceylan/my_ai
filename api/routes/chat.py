from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from agent.graph import run_agent
import json

router = APIRouter()


class ChatRequest(BaseModel):
    message: str
    session_id: str = "default"
    stream: bool = False


class ChatResponse(BaseModel):
    response: str
    session_id: str
    sources: list = []


@router.post("/", response_model=ChatResponse)
async def chat(request: ChatRequest):
    try:
        result = await run_agent(
            message=request.message,
            session_id=request.session_id,
        )
        return ChatResponse(
            response=result["response"],
            session_id=request.session_id,
            sources=result.get("sources", []),
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/stream")
async def chat_stream(request: ChatRequest):
    async def generate():
        async for chunk in run_agent(
            message=request.message,
            session_id=request.session_id,
            stream=True,
        ):
            yield f"data: {json.dumps({'chunk': chunk})}\n\n"
        yield "data: [DONE]\n\n"

    return StreamingResponse(generate(), media_type="text/event-stream")

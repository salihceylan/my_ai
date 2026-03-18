from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session
from api.database import get_db, Message, User
from api.auth import get_current_user
from agent.graph import run_agent

router = APIRouter()


class ChatRequest(BaseModel):
    message: str
    session_id: str = "default"


class ChatResponse(BaseModel):
    response: str
    session_id: str
    sources: list = []


@router.post("/", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    try:
        result = await run_agent(
            message=request.message,
            session_id=f"{current_user.id}_{request.session_id}",
            user_profile=current_user.profile or {},
        )

        db.add(Message(user_id=current_user.id, session_id=request.session_id, role="user", content=request.message))
        db.add(Message(user_id=current_user.id, session_id=request.session_id, role="ai", content=result["response"], sources=result.get("sources", [])))
        db.commit()

        msg_count = db.query(Message).filter(Message.user_id == current_user.id).count()
        if msg_count % 10 == 0:
            await update_user_profile(current_user, db)

        return ChatResponse(response=result["response"], session_id=request.session_id, sources=result.get("sources", []))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


async def update_user_profile(user: User, db: Session):
    messages = (
        db.query(Message)
        .filter(Message.user_id == user.id, Message.role == "user")
        .order_by(Message.created_at.desc())
        .limit(30)
        .all()
    )
    if not messages:
        return

    topics = {}
    total_len = 0
    for m in messages:
        total_len += len(m.content)
        for w in m.content.lower().split():
            if len(w) > 4:
                topics[w] = topics.get(w, 0) + 1

    top_topics = [t[0] for t in sorted(topics.items(), key=lambda x: x[1], reverse=True)[:10]]
    avg_len = total_len // len(messages)

    profile = user.profile or {}
    profile["top_topics"] = top_topics
    profile["avg_message_length"] = avg_len
    profile["message_count"] = db.query(Message).filter(Message.user_id == user.id).count()
    profile["style"] = "detaylı" if avg_len > 100 else "kısa"

    user.profile = profile
    db.commit()

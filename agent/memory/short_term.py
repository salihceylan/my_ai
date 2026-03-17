import redis.asyncio as redis
import json
import os
from langchain_core.messages import HumanMessage, AIMessage


def get_redis():
    return redis.from_url(os.getenv("REDIS_URL", "redis://redis:6379"))


def serialize_messages(messages):
    result = []
    for m in messages:
        if isinstance(m, HumanMessage):
            result.append({"role": "human", "content": m.content})
        elif isinstance(m, AIMessage):
            result.append({"role": "ai", "content": m.content})
    return result


def deserialize_messages(data):
    messages = []
    for m in data:
        if m["role"] == "human":
            messages.append(HumanMessage(content=m["content"]))
        elif m["role"] == "ai":
            messages.append(AIMessage(content=m["content"]))
    return messages


async def get_history(session_id: str, max_messages: int = 20):
    r = get_redis()
    key = f"session:{session_id}"
    data = await r.get(key)
    await r.aclose()

    if not data:
        return []

    messages = deserialize_messages(json.loads(data))
    return messages[-max_messages:]


async def save_history(session_id: str, messages: list, ttl: int = 3600):
    r = get_redis()
    key = f"session:{session_id}"
    serialized = serialize_messages(messages)
    await r.set(key, json.dumps(serialized), ex=ttl)
    await r.aclose()


async def clear_history(session_id: str):
    r = get_redis()
    await r.delete(f"session:{session_id}")
    await r.aclose()

from fastapi import APIRouter, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
import os

router = APIRouter()
security = HTTPBearer()

SECRET_KEY = os.getenv("API_SECRET_KEY", "degistir")


def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    if credentials.credentials != SECRET_KEY:
        raise HTTPException(status_code=401, detail="Yetkisiz erişim")
    return credentials.credentials


class ModelRequest(BaseModel):
    model_name: str


@router.get("/status", dependencies=[Depends(verify_token)])
async def system_status():
    import httpx
    status = {}

    try:
        async with httpx.AsyncClient() as client:
            r = await client.get(f"{os.getenv('OLLAMA_URL')}/api/tags", timeout=5)
            models = [m["name"] for m in r.json().get("models", [])]
            status["ollama"] = {"ok": True, "models": models}
    except Exception:
        status["ollama"] = {"ok": False}

    return status


@router.post("/pull-model", dependencies=[Depends(verify_token)])
async def pull_model(request: ModelRequest):
    import httpx
    async with httpx.AsyncClient(timeout=300) as client:
        r = await client.post(
            f"{os.getenv('OLLAMA_URL')}/api/pull",
            json={"name": request.model_name},
        )
    return {"status": "pulled", "model": request.model_name}

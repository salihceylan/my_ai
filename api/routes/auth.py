from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from pydantic import BaseModel
from api.database import get_db, User
from api.auth import hash_password, verify_password, create_token, get_current_user
import os

router = APIRouter()


class RegisterRequest(BaseModel):
    username: str
    password: str
    admin_key: str


@router.post("/login")
async def login(form: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == form.username).first()
    if not user or not verify_password(form.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Kullanıcı adı veya şifre hatalı")
    return {"access_token": create_token(user.id), "token_type": "bearer", "username": user.username}


@router.post("/register")
async def register(req: RegisterRequest, db: Session = Depends(get_db)):
    if req.admin_key != os.getenv("API_SECRET_KEY"):
        raise HTTPException(status_code=403, detail="Geçersiz admin anahtarı")
    if db.query(User).filter(User.username == req.username).first():
        raise HTTPException(status_code=400, detail="Bu kullanıcı adı zaten alınmış")
    user = User(username=req.username, password_hash=hash_password(req.password))
    db.add(user)
    db.commit()
    db.refresh(user)
    return {"id": user.id, "username": user.username}


@router.get("/me")
async def me(current_user: User = Depends(get_current_user)):
    return {"id": current_user.id, "username": current_user.username, "profile": current_user.profile}

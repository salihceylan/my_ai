from fastapi import APIRouter, UploadFile, File, HTTPException, Form
from pydantic import BaseModel
from pipeline.indexer import index_document, index_url, delete_document, list_documents
import shutil
import os

router = APIRouter()


class UrlRequest(BaseModel):
    url: str
    category: str = "general"


class DocumentResponse(BaseModel):
    id: str
    filename: str
    category: str
    status: str


@router.post("/upload", response_model=DocumentResponse)
async def upload_document(
    file: UploadFile = File(...),
    category: str = Form(default="general"),
):
    allowed = [".pdf", ".docx", ".txt", ".md", ".csv", ".xlsx"]
    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in allowed:
        raise HTTPException(status_code=400, detail=f"Desteklenmeyen format: {ext}")

    tmp_path = f"/tmp/{file.filename}"
    with open(tmp_path, "wb") as f:
        shutil.copyfileobj(file.file, f)

    result = await index_document(tmp_path, category=category)
    os.remove(tmp_path)

    return DocumentResponse(
        id=result["id"],
        filename=file.filename,
        category=category,
        status="indexed",
    )


@router.post("/url")
async def add_url(request: UrlRequest):
    result = await index_url(request.url, category=request.category)
    return {"status": "indexed", "url": request.url, "chunks": result["chunks"]}


@router.get("/")
async def get_documents():
    docs = await list_documents()
    return {"documents": docs}


@router.delete("/{doc_id}")
async def remove_document(doc_id: str):
    await delete_document(doc_id)
    return {"status": "deleted", "id": doc_id}

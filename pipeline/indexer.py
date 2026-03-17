from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
from pipeline.loader import load_file, load_url
from pipeline.splitter import split_texts
from pipeline.embedder import embed_texts
import uuid
import os


def get_qdrant():
    return QdrantClient(url=os.getenv("QDRANT_URL", "http://qdrant:6333"))


def ensure_collection(client: QdrantClient, collection: str, vector_size: int = 768):
    existing = [c.name for c in client.get_collections().collections]
    if collection not in existing:
        client.create_collection(
            collection_name=collection,
            vectors_config=VectorParams(size=vector_size, distance=Distance.COSINE),
        )


async def index_document(file_path: str, category: str = "general") -> dict:
    collection = os.getenv("QDRANT_COLLECTION", "my_ai_docs")
    client = get_qdrant()

    texts = await load_file(file_path)
    chunks = split_texts(texts)
    vectors = embed_texts(chunks)

    ensure_collection(client, collection, vector_size=len(vectors[0]))

    doc_id = str(uuid.uuid4())
    filename = os.path.basename(file_path)

    points = [
        PointStruct(
            id=str(uuid.uuid4()),
            vector=vec,
            payload={
                "text": chunk,
                "source": filename,
                "doc_id": doc_id,
                "category": category,
            },
        )
        for chunk, vec in zip(chunks, vectors)
    ]

    client.upsert(collection_name=collection, points=points)

    return {"id": doc_id, "chunks": len(points)}


async def index_url(url: str, category: str = "web") -> dict:
    collection = os.getenv("QDRANT_COLLECTION", "my_ai_docs")
    client = get_qdrant()

    texts = await load_url(url)
    chunks = split_texts(texts)
    vectors = embed_texts(chunks)

    ensure_collection(client, collection, vector_size=len(vectors[0]))

    doc_id = str(uuid.uuid4())

    points = [
        PointStruct(
            id=str(uuid.uuid4()),
            vector=vec,
            payload={
                "text": chunk,
                "source": url,
                "doc_id": doc_id,
                "category": category,
            },
        )
        for chunk, vec in zip(chunks, vectors)
    ]

    client.upsert(collection_name=collection, points=points)
    return {"id": doc_id, "chunks": len(points)}


async def delete_document(doc_id: str):
    collection = os.getenv("QDRANT_COLLECTION", "my_ai_docs")
    client = get_qdrant()
    client.delete(
        collection_name=collection,
        points_selector={"filter": {"must": [{"key": "doc_id", "match": {"value": doc_id}}]}},
    )


async def list_documents() -> list:
    collection = os.getenv("QDRANT_COLLECTION", "my_ai_docs")
    client = get_qdrant()
    try:
        results, _ = client.scroll(
            collection_name=collection,
            limit=100,
            with_payload=True,
            with_vectors=False,
        )
        seen = {}
        for r in results:
            doc_id = r.payload.get("doc_id")
            if doc_id and doc_id not in seen:
                seen[doc_id] = {
                    "id": doc_id,
                    "source": r.payload.get("source"),
                    "category": r.payload.get("category"),
                }
        return list(seen.values())
    except Exception:
        return []

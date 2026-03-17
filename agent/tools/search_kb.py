from langchain_core.tools import tool
from qdrant_client import QdrantClient
from langchain_ollama import OllamaEmbeddings
import os


def get_embedder():
    return OllamaEmbeddings(
        model=os.getenv("EMBEDDING_MODEL", "nomic-embed-text"),
        base_url=os.getenv("OLLAMA_URL", "http://ollama:11434"),
    )


def get_qdrant():
    return QdrantClient(url=os.getenv("QDRANT_URL", "http://qdrant:6333"))


@tool
def search_knowledge_base(query: str) -> str:
    """Şirket bilgi tabanında ve yüklenen dökümanlar arasında arama yapar."""
    try:
        embedder = get_embedder()
        client = get_qdrant()
        collection = os.getenv("QDRANT_COLLECTION", "my_ai_docs")

        query_vector = embedder.embed_query(query)

        results = client.search(
            collection_name=collection,
            query_vector=query_vector,
            limit=5,
            score_threshold=0.2,
        )

        if not results:
            return "Bilgi tabanında ilgili içerik bulunamadı."

        output = []
        for r in results:
            source = r.payload.get("source", "Bilinmiyor")
            text = r.payload.get("text", "")
            score = round(r.score, 2)
            output.append(f"[Kaynak: {source} | Skor: {score}]\n{text}")

        return "\n\n---\n\n".join(output)

    except Exception as e:
        return f"Bilgi tabanı araması başarısız: {str(e)}"

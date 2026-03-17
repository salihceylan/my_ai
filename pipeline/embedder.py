from langchain_ollama import OllamaEmbeddings
import os


def get_embedder():
    return OllamaEmbeddings(
        model=os.getenv("EMBEDDING_MODEL", "nomic-embed-text"),
        base_url=os.getenv("OLLAMA_URL", "http://ollama:11434"),
    )


def embed_texts(texts: list[str]) -> list[list[float]]:
    """Metinleri vektöre çevirir."""
    embedder = get_embedder()
    return embedder.embed_documents(texts)

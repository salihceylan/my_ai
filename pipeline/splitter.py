from langchain_text_splitters import RecursiveCharacterTextSplitter
import os


def split_texts(texts: list[str]) -> list[str]:
    """Metinleri chunk'lara böler."""
    chunk_size = int(os.getenv("CHUNK_SIZE", 512))
    chunk_overlap = int(os.getenv("CHUNK_OVERLAP", 50))

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        separators=["\n\n", "\n", ".", " ", ""],
    )

    full_text = "\n\n".join(texts)
    chunks = splitter.split_text(full_text)
    return [c.strip() for c in chunks if c.strip()]

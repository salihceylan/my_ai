from unstructured.partition.auto import partition
from unstructured.partition.html import partition_html
import httpx
import os


async def load_file(file_path: str) -> list[str]:
    """PDF, Word, Excel, TXT gibi dosyaları okur ve metin listesi döner."""
    elements = partition(filename=file_path)
    texts = [str(e) for e in elements if str(e).strip()]
    return texts


async def load_url(url: str) -> list[str]:
    """Web sayfasını okur ve metin listesi döner."""
    async with httpx.AsyncClient(timeout=30) as client:
        response = await client.get(url, follow_redirects=True)
        response.raise_for_status()
        html = response.text

    elements = partition_html(text=html)
    texts = [str(e) for e in elements if str(e).strip() and len(str(e)) > 30]
    return texts

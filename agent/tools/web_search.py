from langchain_core.tools import tool
from tavily import TavilyClient
import os


@tool
def web_search(query: str) -> str:
    """İnternette güncel bilgi aramak için kullanılır. Bilgi tabanında bulunamayan konular için çağrılır."""
    try:
        api_key = os.getenv("TAVILY_API_KEY")
        if not api_key or api_key.startswith("tvly-buraya"):
            return "Web arama aktif değil. Lütfen .env dosyasına TAVILY_API_KEY ekleyin."

        client = TavilyClient(api_key=api_key)
        results = client.search(
            query=query,
            search_depth="advanced",
            max_results=5,
        )

        output = []
        for r in results.get("results", []):
            title = r.get("title", "")
            url = r.get("url", "")
            content = r.get("content", "")
            output.append(f"[{title}]({url})\n{content}")

        return "\n\n---\n\n".join(output) if output else "Sonuç bulunamadı."

    except Exception as e:
        return f"Web araması başarısız: {str(e)}"

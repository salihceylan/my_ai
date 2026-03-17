from duckduckgo_search import DDGS


def web_search(query: str, max_results: int = 5) -> str:
    """İnternette DuckDuckGo ile arama yapar. API key gerekmez."""
    try:
        results = []
        with DDGS() as ddgs:
            for r in ddgs.text(query, max_results=max_results):
                title = r.get("title", "")
                url = r.get("href", "")
                body = r.get("body", "")
                results.append(f"[{title}]({url})\n{body}")

        return "\n\n---\n\n".join(results) if results else "Sonuç bulunamadı."

    except Exception as e:
        return f"Web araması başarısız: {str(e)}"

from langchain_ollama import ChatOllama
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
from agent.tools.search_kb import search_knowledge_base
from agent.tools.web_search import web_search
from agent.memory.short_term import get_history, save_history
import os

BASE_PROMPT = """Sen şirket içi bir yapay zeka asistanısın.
Aşağıda bilgi tabanı ve/veya web aramasından bulunan bilgiler verilmiştir.
Bu bilgileri kullanarak soruyu Türkçe olarak yanıtla.
Eğer bilgi yoksa bunu belirt. Kaynak göster."""


def build_system_prompt(user_profile: dict) -> str:
    prompt = BASE_PROMPT
    if user_profile:
        notes = []
        topics = user_profile.get("top_topics", [])
        style = user_profile.get("style", "")
        if topics:
            notes.append(f"Bu kullanıcı genellikle şu konularla ilgileniyor: {', '.join(topics[:5])}.")
        if style == "detaylı":
            notes.append("Kullanıcı detaylı açıklamalar tercih ediyor.")
        elif style == "kısa":
            notes.append("Kullanıcı kısa ve öz cevaplar tercih ediyor.")
        if notes:
            prompt += "\n\nKullanıcı Profili:\n" + " ".join(notes)
    return prompt


def get_llm():
    return ChatOllama(
        model=os.getenv("LLM_MODEL", "qwen2.5:1.5b"),
        base_url=os.getenv("OLLAMA_URL", "http://ollama:11434"),
        temperature=0.1,
    )


async def run_agent(message: str, session_id: str = "default", user_profile: dict = {}, stream: bool = False):
    # 1. Bilgi tabanında her zaman ara
    kb_result = search_knowledge_base.invoke({"query": message})

    # 2. KB'de bulunamazsa internette ara
    web_result = ""
    if "bulunamadı" in kb_result.lower() or len(kb_result) < 50:
        web_result = web_search(message)

    # 3. Konuşma geçmişini al
    history = await get_history(session_id)

    # 4. Sistem mesajını ve sonuçları birleştir
    context_parts = [build_system_prompt(user_profile)]
    if kb_result and "bulunamadı" not in kb_result.lower():
        context_parts.append(f"\n--- Bilgi Tabanı ---\n{kb_result}\n---")
    if web_result and "bulunamadı" not in web_result.lower():
        context_parts.append(f"\n--- Web Arama Sonuçları ---\n{web_result}\n---")

    context_prompt = "\n".join(context_parts)

    messages = [SystemMessage(content=context_prompt)] + history + [HumanMessage(content=message)]

    # 4. Modeli çağır
    llm = get_llm()
    response = llm.invoke(messages)
    response_text = response.content

    # 5. Geçmişi kaydet
    await save_history(session_id, history + [HumanMessage(content=message), AIMessage(content=response_text)])

    # 6. Kaynakları çıkar
    sources = []
    if "Kaynak:" in kb_result:
        for line in kb_result.split("\n"):
            if line.startswith("[Kaynak:"):
                sources.append(line)

    return {"response": response_text, "sources": sources}

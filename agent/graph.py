from langchain_ollama import ChatOllama
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
from agent.tools.search_kb import search_knowledge_base
from agent.memory.short_term import get_history, save_history
import os

SYSTEM_PROMPT = """Sen şirket içi bir yapay zeka asistanısın.
Aşağıda ilgili dökümanlardan bulunan bilgiler verilmiştir.
Bu bilgileri kullanarak soruyu Türkçe olarak yanıtla.
Eğer bilgi yoksa bunu belirt. Kaynak göster."""


def get_llm():
    return ChatOllama(
        model=os.getenv("LLM_MODEL", "qwen2.5:1.5b"),
        base_url=os.getenv("OLLAMA_URL", "http://ollama:11434"),
        temperature=0.1,
    )


async def run_agent(message: str, session_id: str = "default", stream: bool = False):
    # 1. Bilgi tabanında her zaman ara
    kb_result = search_knowledge_base.invoke({"query": message})

    # 2. Konuşma geçmişini al
    history = await get_history(session_id)

    # 3. Sistem mesajını ve KB sonuçlarını birleştir
    context_prompt = f"""{SYSTEM_PROMPT}

--- Bilgi Tabanı Sonuçları ---
{kb_result}
--- Son ---"""

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

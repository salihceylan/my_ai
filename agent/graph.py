from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode
from langchain_ollama import ChatOllama
from langchain_core.messages import HumanMessage, SystemMessage
from agent.tools.search_kb import search_knowledge_base
from agent.tools.web_search import web_search
from agent.memory.short_term import get_history, save_history
from typing import TypedDict, Annotated, Sequence
import operator
import os

SYSTEM_PROMPT = """Sen şirket içi bir yapay zeka asistanısın.
Önce bilgi tabanında ara. Bulamazsan internette araştır.
Türkçe cevap ver. Kaynaklarını belirt.
Emin olmadığın konularda bunu açıkça belirt."""

tools = [search_knowledge_base, web_search]


class AgentState(TypedDict):
    messages: Annotated[Sequence, operator.add]
    sources: list


def get_llm():
    return ChatOllama(
        model=os.getenv("LLM_MODEL", "qwen2.5:14b"),
        base_url=os.getenv("OLLAMA_URL", "http://ollama:11434"),
    ).bind_tools(tools)


def call_model(state: AgentState):
    llm = get_llm()
    messages = [SystemMessage(content=SYSTEM_PROMPT)] + list(state["messages"])
    response = llm.invoke(messages)
    return {"messages": [response]}


def should_continue(state: AgentState):
    last = state["messages"][-1]
    if hasattr(last, "tool_calls") and last.tool_calls:
        return "tools"
    return END


def build_graph():
    graph = StateGraph(AgentState)
    graph.add_node("agent", call_model)
    graph.add_node("tools", ToolNode(tools))
    graph.set_entry_point("agent")
    graph.add_conditional_edges("agent", should_continue)
    graph.add_edge("tools", "agent")
    return graph.compile()


agent_graph = build_graph()


async def run_agent(message: str, session_id: str = "default", stream: bool = False):
    history = await get_history(session_id)
    history.append(HumanMessage(content=message))

    result = agent_graph.invoke({"messages": history, "sources": []})

    final = result["messages"][-1]
    response_text = final.content

    await save_history(session_id, history + [final])

    return {"response": response_text, "sources": result.get("sources", [])}

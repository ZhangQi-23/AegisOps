from app.services.vector_store_service import search_similar_chunks
from app.services.langchain_agent_service import run_agent_langchain


def run_rag_agent(
    question: str,
    knowledge_base_id: int,
    top_k: int = 5,
) -> dict:
    """
    联合诊断：
    1. 检索知识库
    2. 调用 Agent 执行只读诊断工具
    3. 结合知识库资料和实时数据生成回答
    """
    question = question.strip()

    if not question:
        raise ValueError("问题不能为空")

    if knowledge_base_id <= 0:
        raise ValueError("知识库 ID 必须大于 0")

    if not 1 <= top_k <= 10:
        raise ValueError("top_k 必须在 1 到 10 之间")

    # 第一步：检索当前知识库的相关文本
    matches = search_similar_chunks(
        query=question,
        knowledge_base_id=knowledge_base_id,
        top_k=top_k,
    )

    context_parts = []
    sources = []

    for index, match in enumerate(matches, start=1):
        metadata = match.get("metadata") or {}
        content = match.get("content") or ""

        if not content.strip():
            continue

        context_parts.append(
            f"[参考资料 {index}]\n"
            f"文档 ID：{metadata.get('document_id', '未知')}\n"
            f"片段序号：{metadata.get('chunk_index', '未知')}\n"
            f"内容：{content}"
        )

        sources.append({
            "chunk_id": str(match.get("id") or ""),
            "document_id": metadata.get("document_id"),
            "chunk_index": metadata.get("chunk_index"),
            "content": content,
            "distance": match.get("distance"),
        })

    if context_parts:
        context = "\n\n".join(context_parts)
    else:
        context = (
            "当前知识库没有检索到可用的参考文本。"
            "不要声称已经从知识库找到依据。"
            "可以根据成功获取的实时诊断数据给出有限的分析，"
            "并明确说明缺少知识库依据。"
        )

    # 第二步：执行 Agent 工具调用，并把检索资料传给模型
    agent_result = run_agent_langchain(
        question=question,
        context=context,
    )

    # 第三步：返回回答、工具调用记录和知识库来源
    return {
        "knowledge_base_id": knowledge_base_id,
        "question": question,
        "answer": agent_result["answer"],
        "retrieved_count": len(sources),
        "sources": sources,
        "tool_calls": agent_result["tool_calls"],
        "tool_call_count": agent_result["tool_call_count"],
        "stopped_by_limit": agent_result.get(
            "stopped_by_limit",
            False,
        ),
    }
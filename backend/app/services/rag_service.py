from app.services.langchain_rag_service import (
    generate_answer_langchain,
)
from app.services.vector_store_service import search_similar_chunks
import hashlib
import logging

from app.services.cache_service import (
    get_json_cache,
    set_json_cache,
)

def answer_question(
    question: str,
    knowledge_base_id: int,
    top_k: int = 5,
    history: list[dict[str, str]] | None = None,
) -> dict:
    """
    RAG 问答：
    1. 从指定知识库检索相关片段
    2. 将片段组织成上下文
    3. 调用 DeepSeek 生成回答
    4. 返回回答和检索来源
    """
    if not question or not question.strip():
        raise ValueError("问题不能为空")

    if knowledge_base_id <= 0:
        raise ValueError("知识库 ID 必须大于 0")

    if top_k < 1 or top_k > 10:
        raise ValueError("top_k 必须在 1 到 10 之间")

    # 仅缓存没有历史上下文的普通问答
    use_cache = not history
    cache_key = None

    if use_cache:
        normalized_question = question.strip()

        # 使用问题哈希构造缓存键，避免问题文本过长
        question_hash = hashlib.sha256(
            normalized_question.encode("utf-8")
        ).hexdigest()

        cache_key = (
            f"aegisops:rag:v2:"
            f"{knowledge_base_id}:{top_k}:{question_hash}"
        )

        logging.info(
            "RAG 缓存检查：use_cache=%s，key=%s",
            use_cache,
            cache_key,
        )

        try:
            cached_result = get_json_cache(cache_key)

            if isinstance(cached_result, dict):
                logging.info("RAG 缓存命中")
                return cached_result

        except Exception:
            # 缓存异常不能阻断正常问答
            logging.warning(
                "读取 RAG 缓存失败，将执行正常检索",
                exc_info=True,
            )

    matches = search_similar_chunks(
        query=question.strip(),
        knowledge_base_id=knowledge_base_id,
        top_k=top_k,
    )

    # 没有检索到资料时，不让模型凭空生成知识库答案
    if not matches:
        return {
            "answer": (
                "当前知识库没有检索到可用的参考资料，"
                "暂时无法根据该知识库回答这个问题。"
                "请确认文档已经上传、处理成功，"
                "并尝试使用更贴近文档内容的提问方式。"
            ),
            "sources": [],
            "retrieved_count": 0,
        }

    context_parts = []

    for index, match in enumerate(matches, start=1):
        metadata = match.get("metadata") or {}

        context_parts.append(
            f"[参考资料 {index}]\n"
            f"文档 ID：{metadata.get('document_id', '未知')}\n"
            f"片段序号：{metadata.get('chunk_index', '未知')}\n"
            f"内容：{match.get('content', '')}"
        )

    context = "\n\n".join(context_parts)

    answer = generate_answer_langchain(
        question=question,
        context=context,
        history=history,
    )

    sources = []

    for match in matches:
        metadata = match.get("metadata") or {}

        sources.append(
            {
                "chunk_id": match.get("id"),
                "document_id": metadata.get("document_id"),
                "chunk_index": metadata.get("chunk_index"),
                "content": match.get("content"),
                "distance": match.get("distance"),
            }
        )

    result = {
        "answer": answer,
        "sources": sources,
        "retrieved_count": len(matches),
    }

    # 只缓存成功检索并生成答案的普通问答
    if use_cache and cache_key:
        try:
            set_json_cache(
                key=cache_key,
                value=result,
                ttl_seconds=300,
            )
            logging.info(
                "RAG 缓存写入成功，key=%s",
                cache_key,
            )

        except Exception:
            # 写入失败不影响已经生成的答案
            logging.warning(
                "写入 RAG 缓存失败",
                exc_info=True,
            )

    return result
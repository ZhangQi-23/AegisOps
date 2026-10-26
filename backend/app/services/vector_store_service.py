from functools import lru_cache
from pathlib import Path

import chromadb

from app.services.embedding_service import encode_texts, encode_query


# 当前文件位于 backend/app/services/ 下
# parents[2] 对应 backend 目录
BACKEND_DIR = Path(__file__).resolve().parents[2]
CHROMA_DIR = BACKEND_DIR / "chroma_db"

COLLECTION_NAME = "aegisops_knowledge"


@lru_cache(maxsize=1)
def get_chroma_collection():
    """
    获取持久化的 Chroma collection。
    首次调用时创建，后续调用复用。
    """
    client = chromadb.PersistentClient(path=str(CHROMA_DIR))

    collection = client.get_or_create_collection(
        name=COLLECTION_NAME,
        metadata={"hnsw:space": "cosine"},
    )

    return collection



def upsert_document_chunks(
    document_id: int,
    knowledge_base_id: int,
    chunks: list[dict],
) -> None:
    """
    更新指定文档在 Chroma 中的向量。

    先生成并写入新向量，再清理多余的旧向量，
    避免生成新向量之前就删除全部旧数据。
    """
    collection = get_chroma_collection()

    # 获取当前文档已有的向量 ID
    existing = collection.get(
        where={"document_id": document_id},
        include=["metadatas"],
    )
    old_ids = existing["ids"]

    # 没有新文本块时，删除该文档的旧向量
    if not chunks:
        if old_ids:
            collection.delete(ids=old_ids)
        return

    # 1. 先生成新向量
    contents = [item["content"] for item in chunks]
    embeddings = encode_texts(contents)

    ids = [
        f"doc_{document_id}_chunk_{item['chunk_index']}"
        for item in chunks
    ]

    metadatas = [
        {
            "document_id": document_id,
            "knowledge_base_id": knowledge_base_id,
            "chunk_index": item["chunk_index"],
        }
        for item in chunks
    ]

    # 2. 先写入或更新新向量
    collection.upsert(
        ids=ids,
        documents=contents,
        embeddings=embeddings,
        metadatas=metadatas,
    )

    # 3. 新向量写入成功后，再删除不再需要的旧向量
    new_id_set = set(ids)
    stale_ids = [
        item_id
        for item_id in old_ids
        if item_id not in new_id_set
    ]

    if stale_ids:
        collection.delete(ids=stale_ids)



def delete_document_chunks(document_id: int) -> None:
    """
    删除指定文档在 Chroma 中的全部向量。
    """
    collection = get_chroma_collection()

    collection.delete(
        where={"document_id": document_id}
    )


def search_similar_chunks(
    query: str,
    knowledge_base_id: int,
    top_k: int = 5,
) -> list[dict]:
    """
    在指定知识库内，查找与问题最相似的文本块。
    """
    if not query or not query.strip():
        raise ValueError("检索问题不能为空")

    if top_k < 1:
        raise ValueError("top_k 必须大于 0")

    collection = get_chroma_collection()

    # 该知识库还没有向量时，直接返回空结果
    if collection.count() == 0:
        return []

    query_embedding = encode_query(query)

    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=min(top_k, collection.count()),
        where={"knowledge_base_id": knowledge_base_id},
        include=["documents", "metadatas", "distances"],
    )

    matches = []

    ids = results["ids"][0]
    documents = results["documents"][0]
    metadatas = results["metadatas"][0]
    distances = results["distances"][0]

    for item_id, content, metadata, distance in zip(
        ids, documents, metadatas, distances
    ):
        matches.append(
            {
                "id": item_id,
                "content": content,
                "metadata": metadata,
                "distance": distance,
            }
        )

    return matches

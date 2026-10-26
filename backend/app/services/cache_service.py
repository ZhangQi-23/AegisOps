
import json
from typing import Any

from app.core.redis_client import redis_client


DEFAULT_CACHE_TTL = 300  # 默认缓存 5 分钟


def get_json_cache(key: str) -> Any | None:
    """
    读取 JSON 缓存。
    缓存不存在时返回 None。
    """
    if not key:
        raise ValueError("缓存 key 不能为空")

    value = redis_client.get(key)

    if value is None:
        return None

    return json.loads(value)


def set_json_cache(
    key: str,
    value: Any,
    ttl_seconds: int = DEFAULT_CACHE_TTL,
) -> None:
    """
    写入 JSON 缓存，并设置过期时间。
    """
    if not key:
        raise ValueError("缓存 key 不能为空")

    if ttl_seconds <= 0:
        raise ValueError("缓存过期时间必须大于 0")

    serialized = json.dumps(
        value,
        ensure_ascii=False,
    )

    redis_client.set(
        key,
        serialized,
        ex=ttl_seconds,
    )


def delete_cache(key: str) -> bool:
    """
    删除指定缓存。
    """
    if not key:
        raise ValueError("缓存 key 不能为空")

    return bool(redis_client.delete(key))


def delete_knowledge_base_cache(
    knowledge_base_id: int,
) -> int:
    """
    删除指定知识库的所有 RAG 答案缓存。
    兼容 v1、v2 缓存键，返回删除的缓存数量。
    """
    if knowledge_base_id <= 0:
        raise ValueError("知识库 ID 必须大于 0")

    deleted_count = 0

    # 精确匹配版本和知识库 ID，避免误删其他知识库的缓存
    for version in ("v1", "v2"):
        pattern = (
            f"aegisops:rag:{version}:"
            f"{knowledge_base_id}:*"
        )

        # 使用 scan_iter，避免阻塞式 KEYS *
        for key in redis_client.scan_iter(
            match=pattern,
            count=100,
        ):
            deleted_count += redis_client.delete(key)

    return deleted_count

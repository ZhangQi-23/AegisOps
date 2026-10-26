
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
    返回删除的缓存数量。
    """
    if knowledge_base_id <= 0:
        raise ValueError("知识库 ID 必须大于 0")

    pattern = f"aegisops:rag:v1:{knowledge_base_id}:*"

    deleted_count = 0

    # 使用 scan_iter 避免对 Redis 执行阻塞式的 KEYS *
    for key in redis_client.scan_iter(match=pattern, count=100):
        deleted_count += redis_client.delete(key)

    return deleted_count


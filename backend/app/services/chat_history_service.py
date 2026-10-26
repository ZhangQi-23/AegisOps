import json
import re

from app.core.redis_client import redis_client


# 会话历史保存 24 小时
CHAT_HISTORY_TTL = 24 * 60 * 60

# 每个会话最多保留最近 20 条消息
MAX_HISTORY_MESSAGES = 20

# 限制单条消息的长度，避免历史数据无限膨胀
MAX_MESSAGE_LENGTH = 4000


def _get_history_key(user_id: int, session_id: str) -> str:
    """
    生成用户隔离的会话 Redis Key。
    同一个 session_id 在不同用户下对应不同 Key。
    """
    if user_id <= 0:
        raise ValueError("user_id 必须大于 0")

    if not session_id or not re.fullmatch(
        r"[a-zA-Z0-9_-]{1,64}", session_id
    ):
        raise ValueError("session_id 格式无效")

    return f"aegisops:chat:{user_id}:{session_id}"


def add_message(
    user_id: int,
    session_id: str,
    role: str,
    content: str,
) -> None:
    """
    添加一条对话消息，并刷新会话 TTL。
    role 仅允许 user 或 assistant。
    """
    if role not in {"user", "assistant"}:
        raise ValueError("role 只能是 user 或 assistant")

    if not isinstance(content, str) or not content.strip():
        raise ValueError("消息内容不能为空")

    if len(content) > MAX_MESSAGE_LENGTH:
        raise ValueError(
            f"消息长度不能超过 {MAX_MESSAGE_LENGTH} 个字符"
        )

    key = _get_history_key(user_id, session_id)

    message = {
        "role": role,
        "content": content.strip(),
    }

    # 追加消息、保留最近 N 条，并刷新过期时间
    with redis_client.pipeline(transaction=True) as pipe:
        pipe.rpush(
            key,
            json.dumps(message, ensure_ascii=False),
        )
        pipe.ltrim(key, -MAX_HISTORY_MESSAGES, -1)
        pipe.expire(key, CHAT_HISTORY_TTL)
        pipe.execute()


def get_history(
    user_id: int,
    session_id: str,
) -> list[dict[str, str]]:
    """
    按时间顺序获取会话历史。
    查询历史不会自动延长 TTL。
    """
    key = _get_history_key(user_id, session_id)

    raw_messages = redis_client.lrange(
        key,
        0,
        -1,
    )

    history = []

    for raw_message in raw_messages:
        message = json.loads(raw_message)

        if (
            isinstance(message, dict)
            and message.get("role") in {"user", "assistant"}
            and isinstance(message.get("content"), str)
        ):
            history.append({
                "role": message["role"],
                "content": message["content"],
            })

    return history


def clear_history(
    user_id: int,
    session_id: str,
) -> bool:
    """
    删除当前用户指定会话的历史。
    不影响其他用户或其他会话。
    """
    key = _get_history_key(user_id, session_id)

    return bool(redis_client.delete(key))


def get_history_ttl(
    user_id: int,
    session_id: str,
) -> int:
    """
    返回剩余有效秒数。
    -2 表示 Key 不存在；-1 表示没有设置过期时间。
    """
    key = _get_history_key(user_id, session_id)

    return redis_client.ttl(key)

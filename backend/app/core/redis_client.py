import redis


# 创建 Redis 客户端
redis_client = redis.Redis(
    host="127.0.0.1",
    port=6379,
    db=0,
    decode_responses=True,
    protocol=2
)


def get_redis():
    """
    获取 Redis 客户端
    """
    return redis_client
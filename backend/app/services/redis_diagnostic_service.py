from app.core.redis_client import redis_client


def check_redis_connection() -> dict:
    """检查 Redis 是否可连接。只读操作。"""
    try:
        result = redis_client.ping()

        return {
            "tool": "check_redis_connection",
            "success": bool(result),
            "data": {
                "connected": bool(result),
                "message": "Redis 连接正常" if result else "Redis 未返回正常响应",
            },
            "error": None,
        }
    except Exception as exc:
        return {
            "tool": "check_redis_connection",
            "success": False,
            "data": None,
            "error": f"Redis 连接检查失败：{type(exc).__name__}",
        }


def get_redis_memory_info() -> dict:
    """获取 Redis 内存指标。只读操作。"""
    try:
        info = redis_client.info("memory")

        fields = [
            "used_memory",
            "used_memory_human",
            "used_memory_peak",
            "used_memory_peak_human",
            "maxmemory",
            "maxmemory_human",
            "mem_fragmentation_ratio",
        ]

        memory = {
            key: info[key]
            for key in fields
            if key in info
        }

        return {
            "tool": "get_redis_memory_info",
            "success": True,
            "data": memory,
            "error": None,
        }
    except Exception as exc:
        return {
            "tool": "get_redis_memory_info",
            "success": False,
            "data": None,
            "error": f"获取 Redis 内存信息失败：{type(exc).__name__}",
        }


def get_redis_server_info() -> dict:
    """获取 Redis 服务运行信息。只读操作。"""
    try:
        info = redis_client.info("server")
        clients = redis_client.info("clients")

        server_fields = [
            "redis_version",
            "uptime_in_seconds",
            "uptime_in_days",
        ]

        client_fields = [
            "connected_clients",
            "blocked_clients",
        ]

        data = {
            key: info[key]
            for key in server_fields
            if key in info
        }

        data.update({
            key: clients[key]
            for key in client_fields
            if key in clients
        })

        return {
            "tool": "get_redis_server_info",
            "success": True,
            "data": data,
            "error": None,
        }
    except Exception as exc:
        return {
            "tool": "get_redis_server_info",
            "success": False,
            "data": None,
            "error": f"获取 Redis 服务信息失败：{type(exc).__name__}",
        }
import json
from typing import Any, Callable

from app.services.redis_diagnostic_service import (
    check_redis_connection,
    get_redis_memory_info,
    get_redis_server_info,
)


# 只登记经过我们审核的工具，不接受模型提供的任意函数名
TOOLS: dict[str, dict[str, Any]] = {
    "check_redis_connection": {
        "description": "检查 Redis 服务是否能够正常连接。",
        "parameters": {
            "type": "object",
            "properties": {},
            "required": [],
            "additionalProperties": False,
        },
        "function": check_redis_connection,
    },
    "get_redis_memory_info": {
        "description": (
            "查询 Redis 内存使用量、历史峰值、"
            "最大内存配置和内存碎片率。"
        ),
        "parameters": {
            "type": "object",
            "properties": {},
            "required": [],
            "additionalProperties": False,
        },
        "function": get_redis_memory_info,
    },
    "get_redis_server_info": {
        "description": (
            "查询 Redis 版本、运行时长、"
            "当前连接客户端数和阻塞客户端数。"
        ),
        "parameters": {
            "type": "object",
            "properties": {},
            "required": [],
            "additionalProperties": False,
        },
        "function": get_redis_server_info,
    },
}


def get_tool_definitions() -> list[dict[str, Any]]:
    """
    获取发送给支持 OpenAI Tool Calling 格式的大模型的工具定义。
    function 字段是本地执行函数，不发送给模型。
    """
    definitions = []

    for name, tool in TOOLS.items():
        definitions.append(
            {
                "type": "function",
                "function": {
                    "name": name,
                    "description": tool["description"],
                    "parameters": tool["parameters"],
                },
            }
        )

    return definitions


def execute_tool(
    name: str,
    arguments_json: str,
) -> dict[str, Any]:
    """
    执行白名单中的工具。
    只允许已登记的工具，且当前工具不接收任何参数。
    """
    tool = TOOLS.get(name)

    if tool is None:
        return {
            "success": False,
            "error": "不允许调用该工具",
        }

    try:
        arguments = json.loads(arguments_json or "{}")

        if not isinstance(arguments, dict):
            return {
                "success": False,
                "error": "工具参数必须是 JSON 对象",
            }

        # 目前三个工具均不需要参数，拒绝额外参数
        if arguments:
            return {
                "success": False,
                "error": "该工具不接受参数",
            }

        function: Callable[[], dict[str, Any]] = tool["function"]
        result = function()

        # 避免工具执行异常直接中断 Agent 主流程
        if not isinstance(result, dict):
            return {
                "success": False,
                "error": "工具返回了不支持的数据格式",
            }

        return result

    except (json.JSONDecodeError, TypeError, ValueError):
        return {
            "success": False,
            "error": "工具参数格式无效",
        }
    except Exception:
        # 不把异常细节、连接信息等直接暴露给模型
        return {
            "success": False,
            "error": "工具执行失败，请检查后端日志",
        }


from types import SimpleNamespace
from unittest.mock import patch, MagicMock

from app.services import agent_service


def test_agent_stops_at_tool_limit():
    """模拟模型连续请求工具，验证 Agent 会在达到上限后停止。"""

    # 模拟模型每次都请求同一个只读工具
    fake_tool_call = SimpleNamespace(
        id="call_test_001",
        function=SimpleNamespace(
            name="check_redis_connection",
            arguments="{}",
        ),
    )

    fake_message = MagicMock()
    fake_message.content = None
    fake_message.tool_calls = [fake_tool_call]
    fake_message.model_dump.return_value = {
        "role": "assistant",
        "content": None,
        "tool_calls": [
            {
                "id": "call_test_001",
                "type": "function",
                "function": {
                    "name": "check_redis_connection",
                    "arguments": "{}",
                },
            }
        ],
    }

    fake_response = SimpleNamespace(
        choices=[
            SimpleNamespace(message=fake_message)
        ]
    )

    # 模拟 DeepSeek 客户端
    fake_client = MagicMock()
    fake_client.chat.completions.create.return_value = fake_response

    # 模拟工具执行结果，不连接真实 Redis
    fake_tool_result = {
        "tool": "check_redis_connection",
        "success": True,
        "data": {"connected": True},
        "error": None,
    }

    with (
        patch.object(
            agent_service,
            "get_llm_client",
            return_value=fake_client,
        ),
        patch.object(
            agent_service,
            "get_tool_definitions",
            return_value=[],
        ),
        patch.object(
            agent_service,
            "execute_tool",
            return_value=fake_tool_result,
        ) as mock_execute_tool,
    ):
        result = agent_service.run_agent(
            "请检查 Redis 的连接状态"
        )

    # 验证 Agent 在上限处停止
    assert result["stopped_by_limit"] is True
    assert result["tool_call_count"] == agent_service.MAX_TOOL_ROUNDS

    # 每一轮只模拟一个工具调用
    assert mock_execute_tool.call_count == agent_service.MAX_TOOL_ROUNDS

    # 达到上限后不应继续执行新一轮工具
    assert (
        fake_client.chat.completions.create.call_count
        == agent_service.MAX_TOOL_ROUNDS + 1
    )

    print("工具调用次数上限测试通过！")
    print("工具执行次数：", mock_execute_tool.call_count)
    print("模型请求次数：", fake_client.chat.completions.create.call_count)
    print("stopped_by_limit：", result["stopped_by_limit"])
    print("最终回答：", result["answer"])


if __name__ == "__main__":
    test_agent_stops_at_tool_limit()

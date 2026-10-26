
from unittest.mock import MagicMock, patch

from app.services import agent_service


def test_agent_handles_llm_failure():
    """模拟大模型调用失败，检查异常是否被正确传递。"""

    fake_client = MagicMock()

    fake_client.chat.completions.create.side_effect = RuntimeError(
        "模拟 DeepSeek 服务异常"
    )

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
    ):
        try:
            agent_service.run_agent(
                "请检查 Redis 的连接状态"
            )
        except RuntimeError as exc:
            assert str(exc) == "模拟 DeepSeek 服务异常"
            print("模型异常传递测试通过！")
            print("异常类型：", type(exc).__name__)
            print("异常信息：", str(exc))
        else:
            raise AssertionError(
                "预期模型异常向上传递，但 Agent 没有抛出异常"
            )


if __name__ == "__main__":
    test_agent_handles_llm_failure()

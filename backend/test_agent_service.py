
from pprint import pprint

from app.services.agent_service import run_agent


if __name__ == "__main__":
    questions = [
        "检查一下 Redis 的连接状态。",
        "帮我检查 Redis 当前的内存使用情况，并解释各项指标。",
        "查看 Redis 服务版本、运行时间和客户端连接情况。",
    ]

    for question in questions:
        print("\n" + "=" * 60)
        print("用户问题：", question)

        try:
            result = run_agent(question)

            print("\nAgent 回答：")
            print(result["answer"])

            print("\n工具调用记录：")
            pprint(result["tool_calls"], sort_dicts=False)

            print("\n工具调用次数：", result["tool_call_count"])

            if result.get("stopped_by_limit"):
                print("警告：触发工具调用次数上限")

        except Exception as exc:
            print("测试失败：", type(exc).__name__, str(exc))

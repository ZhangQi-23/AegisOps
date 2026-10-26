from app.services.agent_tool_registry import (
    TOOLS,
    get_tool_definitions,
    execute_tool,
)


if __name__ == "__main__":
    definitions = get_tool_definitions()

    print("已注册工具：")
    for item in definitions:
        print("-", item["function"]["name"])

    assert len(definitions) == 3
    assert set(TOOLS) == {
        "check_redis_connection",
        "get_redis_memory_info",
        "get_redis_server_info",
    }

    print("\n测试 1：查询 Redis 内存")
    result = execute_tool(
        "get_redis_memory_info",
        "{}",
    )
    print(result)
    assert result["success"] is True

    print("\n测试 2：拒绝未知工具")
    result = execute_tool(
        "delete_all_data",
        "{}",
    )
    print(result)
    assert result["success"] is False

    print("\n测试 3：拒绝额外参数")
    result = execute_tool(
        "get_redis_memory_info",
        '{"command": "FLUSHALL"}',
    )
    print(result)
    assert result["success"] is False

    print("\n所有工具注册表测试通过！")

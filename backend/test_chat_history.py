from app.services.chat_history_service import (
    add_message,
    get_history,
    clear_history,
    get_history_ttl,
)


if __name__ == "__main__":
    user_id = 999999
    session_id = "test_chat_session"

    # 清理上一次测试遗留的数据
    clear_history(user_id, session_id)

    print("测试 1：保存多轮对话")

    add_message(
        user_id,
        session_id,
        "user",
        "Redis 内存快满了怎么办？",
    )
    add_message(
        user_id,
        session_id,
        "assistant",
        "可以先检查内存使用率和大 Key。",
    )
    add_message(
        user_id,
        session_id,
        "user",
        "那大 Key 怎么检查？",
    )

    history = get_history(user_id, session_id)

    assert len(history) == 3
    assert history[0]["role"] == "user"
    assert history[1]["role"] == "assistant"
    assert history[2]["content"] == "那大 Key 怎么检查？"

    print("历史记录：")
    for item in history:
        print(item)

    print("\n测试 2：检查 TTL")

    ttl = get_history_ttl(user_id, session_id)
    print("剩余秒数：", ttl)

    assert 0 < ttl <= 24 * 60 * 60

    print("\n测试 3：检查用户隔离")

    other_user_history = get_history(
        user_id=999998,
        session_id=session_id,
    )

    assert other_user_history == []
    print("不同用户读取不到彼此的会话历史")

    print("\n测试 4：检查历史条数上限")

    for i in range(25):
        add_message(
            user_id,
            session_id,
            "user",
            f"测试消息 {i}",
        )

    history = get_history(user_id, session_id)

    assert len(history) == 20
    assert history[-1]["content"] == "测试消息 24"

    print("最近 20 条消息保留成功")

    print("\n测试 5：清除历史")

    deleted = clear_history(user_id, session_id)
    history = get_history(user_id, session_id)

    assert deleted is True
    assert history == []

    print("会话清除成功")
    print("\n全部会话历史测试通过！")

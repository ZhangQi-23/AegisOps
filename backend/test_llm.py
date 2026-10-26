from app.services.llm_service import generate_answer


if __name__ == "__main__":
    answer = generate_answer(
        question="Redis 内存使用率过高时应该检查什么？",
        context=(
            "运维规范：Redis 内存使用率持续超过 90% 时，"
            "应检查大 Key、内存碎片率以及异常的缓存增长。"
        ),
    )

    print("DeepSeek 回答：")
    print(answer)
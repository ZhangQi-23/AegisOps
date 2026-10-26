
from app.services.langchain_rag_service import (
    generate_answer_langchain,
)


def main():
    question = "Redis 内存使用率过高时应该检查什么？"

    context = """
    Redis 内存使用率过高时，需要检查大 Key、
    内存碎片率、内存淘汰策略和 Redis 服务状态。
    应结合实际监测指标判断问题，不能仅凭单一指标下结论。
    """

    print("开始测试 LangChain RAG 模型调用...")

    answer = generate_answer_langchain(
        question=question,
        context=context,
    )

    print("\n用户问题：")
    print(question)

    print("\n模型回答：")
    print(answer)

    if not answer.strip():
        raise RuntimeError("回答为空")

    print("\nLangChain RAG 模型调用测试通过！")


if __name__ == "__main__":
    main()

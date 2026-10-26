
from app.services.langchain_llm_service import (
    get_langchain_chat_model,
)


def main():
    print("开始测试 LangChain + DeepSeek...")

    model = get_langchain_chat_model()

    response = model.invoke(
        "请用中文简要介绍 AegisOps 企业智能运维知识助手，"
        "不超过 100 个字。"
    )

    answer = response.content

    if not isinstance(answer, str) or not answer.strip():
        raise RuntimeError("LangChain 没有返回有效文本")

    print("\n模型回答：")
    print(answer.strip())

    print("\nLangChain + DeepSeek 测试通过！")


if __name__ == "__main__":
    main()

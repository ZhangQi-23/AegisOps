import os

from dotenv import load_dotenv
from langchain_openai import ChatOpenAI


# 当前文件位于 backend/app/services/ 下
# parents[2] 对应 backend 目录
BACKEND_DIR = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..")
)

ENV_FILE = os.path.join(BACKEND_DIR, ".env")
load_dotenv(ENV_FILE)


def get_langchain_chat_model() -> ChatOpenAI:
    """
    创建 LangChain 使用的 DeepSeek 模型客户端。
    保留原有 OpenAI SDK 客户端，不影响旧业务。
    """
    api_key = os.getenv("LLM_API_KEY")
    model_name = os.getenv("LLM_MODEL")
    base_url = os.getenv(
        "LLM_BASE_URL",
        "https://api.deepseek.com",
    )

    if not api_key:
        raise RuntimeError(
            "未配置 LLM_API_KEY，请检查 backend/.env"
        )

    if not model_name:
        raise RuntimeError(
            "未配置 LLM_MODEL，请检查 backend/.env"
        )

    return ChatOpenAI(
        model=model_name,
        api_key=api_key,
        base_url=base_url,
        timeout=60.0,
        max_retries=2,
        temperature=0.2,
    )

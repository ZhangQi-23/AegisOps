from functools import lru_cache

from sentence_transformers import SentenceTransformer


MODEL_NAME = "BAAI/bge-small-zh-v1.5"


@lru_cache(maxsize=1)
def get_embedding_model() -> SentenceTransformer:
    """
    加载并缓存 Embedding 模型。
    同一进程内重复调用时，不会反复加载模型。
    """
    return SentenceTransformer(MODEL_NAME)


def encode_texts(texts: list[str]) -> list[list[float]]:
    """
    将多段文本转换成向量。
    """
    if not texts:
        return []

    model = get_embedding_model()

    embeddings = model.encode(
        texts,
        normalize_embeddings=True,
        convert_to_numpy=True,
    )

    return embeddings.tolist()


def encode_query(text: str) -> list[float]:
    """
    将用户问题转换成向量。
    """
    if not text or not text.strip():
        raise ValueError("检索问题不能为空")

    return encode_texts([text.strip()])[0]

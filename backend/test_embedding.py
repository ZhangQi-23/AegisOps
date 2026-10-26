from sentence_transformers import SentenceTransformer

# 加载中文 Embedding 模型
model = SentenceTransformer("BAAI/bge-small-zh-v1.5")

texts = [
    "Redis 内存使用率过高时，需要检查大 Key。",
    "缓存占用内存过高时，可以排查大对象。",
    "MySQL 数据库连接失败时，需要检查连接池。",
]

# 将文本转换成向量
embeddings = model.encode(texts, normalize_embeddings=True)

print("向量数量：", len(embeddings))
print("单个向量的维度：", len(embeddings[0]))
print("第一段文本的向量前 10 个数字：")
print(embeddings[0][:10])

# 比较第一段与其他文本的语义相似度
similarities = embeddings @ embeddings[0]

print("\n与第一段文本的相似度：")
for text, score in zip(texts, similarities):
    print(f"{score:.4f}  {text}")


from app.services.vector_store_service import search_similar_chunks


results = search_similar_chunks(
    query="缓存占用内存太多怎么办？",
    knowledge_base_id=2,
    top_k=3,
)

if not results:
    print("没有找到相关文本，请先确认文档已经处理完成。")
else:
    for index, item in enumerate(results, start=1):
        print(f"\n第 {index} 条结果")
        print("文档信息：", item["metadata"])
        print("距离分数：", round(item["distance"], 4))
        print("文本内容：", item["content"])

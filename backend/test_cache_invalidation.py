
from app.services.cache_service import (
    get_json_cache,
    set_json_cache,
    delete_knowledge_base_cache,
)

if __name__ == "__main__":
    # 使用独立的测试键，避免误删真实业务缓存
    key_2 = "aegisops:rag:v1:2:5:cache_test_001"
    key_20 = "aegisops:rag:v1:20:5:cache_test_002"

    # 准备测试数据
    set_json_cache(key_2, {"answer": "知识库 2"})
    set_json_cache(key_20, {"answer": "知识库 20"})

    # 清理知识库 2 的缓存
    deleted = delete_knowledge_base_cache(2)

    assert deleted >= 1
    assert get_json_cache(key_2) is None
    assert get_json_cache(key_20) == {"answer": "知识库 20"}

    # 清理测试数据
    from app.services.cache_service import delete_cache
    delete_cache(key_20)

    print("缓存失效测试全部通过！")

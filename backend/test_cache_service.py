
from app.services.cache_service import (
    get_json_cache,
    set_json_cache,
    delete_cache,
)

if __name__ == "__main__":
    key = "aegisops:test:cache_001"

    # 清理旧测试数据
    delete_cache(key)

    print("测试 1：读取不存在的缓存")
    assert get_json_cache(key) is None
    print("通过")

    print("\n测试 2：写入并读取缓存")
    data = {
        "question": "Redis 内存过高怎么办？",
        "answer": "检查内存指标和大 Key。",
        "sources": [{"document_id": 1}],
    }

    set_json_cache(key, data, ttl_seconds=60)

    result = get_json_cache(key)
    assert result == data
    print("通过")

    print("\n测试 3：删除缓存")
    deleted = delete_cache(key)

    assert deleted is True
    assert get_json_cache(key) is None
    print("通过")

    print("\n全部缓存服务测试通过！")

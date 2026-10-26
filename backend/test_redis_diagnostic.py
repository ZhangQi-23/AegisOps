from pprint import pprint

from app.services.redis_diagnostic_service import (
    check_redis_connection,
    get_redis_memory_info,
    get_redis_server_info,
)


def run_test(name, func):
    print(f"\n{'=' * 20} {name} {'=' * 20}")
    result = func()
    pprint(result, sort_dicts=False)

    if not result["success"]:
        print(f"测试失败：{result['error']}")
        return False

    print("测试通过")
    return True


if __name__ == "__main__":
    results = [
        run_test("Redis 连接检查", check_redis_connection),
        run_test("Redis 内存信息", get_redis_memory_info),
        run_test("Redis 服务信息", get_redis_server_info),
    ]

    print(f"\n测试结果：{sum(results)}/{len(results)} 项通过")
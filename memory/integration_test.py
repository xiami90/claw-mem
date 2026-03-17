#!/usr/bin/env python3
"""
integration_test.py - 整合测试
验证所有模块协同工作

测试场景：
1. 事件隔离存储
2. 跨事件搜索
3. 轨迹记录
4. 热度评分
"""

import sys
from pathlib import Path

# 添加模块路径
sys.path.insert(0, "/root/.openclaw/workspace/memory")

from event_directories import DirectoryManager, EventType
from embedding_engine import SmartEmbedder, LocalEmbedder
from event_router import EventRouter, SmartRouter
from trace_recorder import TraceRecorder, TraceContext
from hotness_scorer import ImportanceScorer, MemoryLifecycleManager
from enhanced_memory_system import EnhancedFourLayerSystem


def test_event_isolation():
    """测试事件隔离"""
    print("\n" + "=" * 60)
    print("测试 1: 事件隔离存储")
    print("=" * 60)
    
    system = EnhancedFourLayerSystem()
    
    # 存储不同事件类型的记忆
    test_memories = [
        ("比亚迪预测", "预测比亚迪今日上涨2%", EventType.FINANCIAL, "投资"),
        ("孙子兵法", "始计篇学习完成", EventType.MILITARY, "学习"),
        ("/ic 命令", "IronClaw API 调用", EventType.IRONCLAW, "开发"),
        ("HEARTBEAT", "系统心跳检查", EventType.SYSTEM, "系统"),
    ]
    
    for topic, content, event_type, category in test_memories:
        result = system.store(topic, content, event_type, category)
        print(f"   ✅ {topic} → {event_type.value}")
    
    # 验证隔离
    from pathlib import Path
    base_path = Path("/root/.openclaw/workspace/memory/l2_memories")
    
    for event_type in [EventType.FINANCIAL, EventType.MILITARY]:
        event_path = base_path / event_type.value
        if event_path.exists():
            memories_file = event_path / "memories.json"
            if memories_file.exists():
                import json
                with open(memories_file, 'r') as f:
                    data = json.load(f)
                print(f"   📂 {event_type.value}: {len(data.get('memories', []))}条记忆")
    
    return True


def test_event_routing():
    """测试事件路由"""
    print("\n" + "=" * 60)
    print("测试 2: 事件路由")
    print("=" * 60)
    
    router = EventRouter()
    
    test_queries = [
        ("比亚迪今天怎么样？", EventType.FINANCIAL),
        ("孙子兵法学到哪了？", EventType.MILITARY),
        ("/ic 你好", EventType.IRONCLAW),
        ("HEARTBEAT 检查", EventType.SYSTEM),
        ("今天天气", EventType.TEMP),
    ]
    
    passed = 0
    for query, expected_type in test_queries:
        result = router.route(query)
        is_correct = result.event_type == expected_type
        status = "✅" if is_correct else "❌"
        print(f"   {status} '{query}' → {result.event_type.value} (置信度: {result.confidence:.2f})")
        if is_correct:
            passed += 1
    
    accuracy = passed / len(test_queries) * 100
    print(f"\n   准确率: {accuracy:.1f}% ({passed}/{len(test_queries)})")
    
    return accuracy >= 60


def test_search_with_trace():
    """测试搜索和轨迹"""
    print("\n" + "=" * 60)
    print("测试 3: 搜索 + 轨迹记录")
    print("=" * 60)
    
    system = EnhancedFourLayerSystem()
    
    # 先存储一些记忆
    system.store("比亚迪预测", "预测比亚迪今日上涨", EventType.FINANCIAL, "投资")
    system.store("汇川技术分析", "汇川技术基本面良好", EventType.FINANCIAL, "投资")
    
    # 搜索
    result = system.search("比亚迪", limit=5)
    
    print(f"   查询: 比亚迪")
    print(f"   事件识别: {result['event_type']}")
    print(f"   找到: {result['total_found']}条结果")
    
    # 显示轨迹
    if result.get("trace"):
        from trace_recorder import RetrievalTrace
        trace = RetrievalTrace(
            query=result["trace"]["query"],
            event_type=result["trace"]["event_type"],
            steps=[],
            total_found=result["trace"]["total_found"]
        )
        print(f"\n   轨迹:\n{trace.render()}")
    
    return result['total_found'] > 0


def test_hotness_scoring():
    """测试热度评分"""
    print("\n" + "=" * 60)
    print("测试 4: 热度评分")
    print("=" * 60)
    
    from datetime import datetime, timedelta
    scorer = ImportanceScorer()
    
    now = datetime.now()
    
    test_cases = [
        (20, now, "high", "投资", "热门记忆"),
        (5, now - timedelta(days=3), "medium", "项目", "温记忆"),
        (0, now - timedelta(days=30), "low", "default", "冷记忆"),
    ]
    
    for access_count, updated_at, priority, category, desc in test_cases:
        score = scorer.calculate_importance(access_count, updated_at, priority, category)
        print(f"   {desc}: 热度={score.hotness:.3f}, 总分={score.total:.3f}, 等级={score.level}")
    
    return True


def test_lifecycle_management():
    """测试生命周期管理"""
    print("\n" + "=" * 60)
    print("测试 5: 生命周期管理")
    print("=" * 60)
    
    from datetime import datetime, timedelta
    manager = MemoryLifecycleManager()
    
    now = datetime.now()
    
    memories = [
        {"id": 1, "access_count": 20, "last_access": now, "priority": "high", "category": "投资"},
        {"id": 2, "access_count": 5, "last_access": now - timedelta(days=7), "priority": "medium", "category": "项目"},
        {"id": 3, "access_count": 0, "last_access": now - timedelta(days=60), "priority": "low", "category": "default"},
    ]
    
    classified = manager.classify_memories(memories)
    
    print(f"   热记忆: {len(classified['hot'])}条")
    print(f"   温记忆: {len(classified['warm'])}条")
    print(f"   冷记忆: {len(classified['cold'])}条")
    
    archive_candidates = manager.get_archive_candidates(memories)
    print(f"   归档候选: {len(archive_candidates)}条")
    
    return True


def main():
    """运行所有测试"""
    print("=" * 60)
    print("🧪 增强版记忆系统整合测试")
    print("=" * 60)
    
    tests = [
        ("事件隔离存储", test_event_isolation),
        ("事件路由", test_event_routing),
        ("搜索 + 轨迹", test_search_with_trace),
        ("热度评分", test_hotness_scoring),
        ("生命周期管理", test_lifecycle_management),
    ]
    
    results = []
    for name, test_func in tests:
        try:
            passed = test_func()
            results.append((name, passed))
        except Exception as e:
            print(f"\n   ❌ 错误: {e}")
            results.append((name, False))
    
    # 总结
    print("\n" + "=" * 60)
    print("📊 测试总结")
    print("=" * 60)
    
    passed = sum(1 for _, p in results if p)
    total = len(results)
    
    for name, p in results:
        status = "✅ 通过" if p else "❌ 失败"
        print(f"   {status} {name}")
    
    print(f"\n   通过率: {passed/total*100:.1f}% ({passed}/{total})")
    
    if passed == total:
        print("\n   🎉 所有测试通过！")
    
    return passed == total


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

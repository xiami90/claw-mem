#!/usr/bin/env python3
"""
memory_api.py - 记忆系统统一 API
对外提供简洁接口

使用示例：
    from memory_api import MemoryAPI
    
    api = MemoryAPI()
    
    # 存储记忆
    api.remember("比亚迪预测", "预测今日上涨2%", event="financial")
    
    # 搜索记忆
    results = api.recall("比亚迪")
    
    # 查看轨迹
    trace = api.get_trace(results["trace_id"])
"""

from typing import List, Dict, Any, Optional
from datetime import datetime
import logging

from event_directories import EventType
from enhanced_memory_system import EnhancedFourLayerSystem
from cross_event_merger import CrossEventMerger

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MemoryAPI:
    """
    记忆系统统一 API
    
    设计原则：
    1. 简洁易用
    2. 自动路由
    3. 透明追踪
    """
    
    def __init__(self):
        self.system = EnhancedFourLayerSystem()
        self.merger = CrossEventMerger()
        logger.info("🚀 记忆系统 API 初始化完成")
    
    # ==================== 核心操作 ====================
    
    def remember(
        self,
        topic: str,
        content: str,
        event: str = "auto",
        category: str = "general",
        priority: str = "medium"
    ) -> dict:
        """
        存储记忆
        
        Args:
            topic: 主题
            content: 内容
            event: 事件类型 (financial/military/ironclaw/system/temp/auto)
            category: 分类
            priority: 优先级 (high/medium/low)
        
        Returns:
            存储结果
        """
        # 自动识别事件类型
        if event == "auto":
            from event_router import EventRouter
            router = EventRouter()
            routed = router.route(content)
            event_type = routed.event_type
        else:
            event_type = self._parse_event_type(event)
        
        # 存储
        result = self.system.store(
            topic=topic,
            content=content,
            event_type=event_type,
            category=category,
            priority=priority
        )
        
        return {
            "success": True,
            "memory_id": result.get("memory_id"),
            "event": event_type.value,
            "message": f"已存储到 {event_type.value} 事件目录"
        }
    
    def recall(
        self,
        query: str,
        limit: int = 5,
        event: str = None
    ) -> dict:
        """
        搜索记忆
        
        Args:
            query: 查询文本
            limit: 最大结果数
            event: 限定事件类型（可选）
        
        Returns:
            搜索结果
        """
        event_filter = self._parse_event_type(event) if event else None
        
        result = self.system.search(
            query=query,
            limit=limit,
            event_filter=event_filter
        )
        
        return {
            "success": True,
            "query": query,
            "event_detected": result["event_type"],
            "total_found": result["total_found"],
            "results": result["results"],
            "trace": result.get("trace")
        }
    
    def forget(self, memory_id: str, event: str = None) -> dict:
        """
        删除记忆（归档）
        
        注意：实际不删除，只标记为归档
        """
        # TODO: 实现归档逻辑
        return {
            "success": True,
            "message": "已归档",
            "memory_id": memory_id
        }
    
    # ==================== 状态查询 ====================
    
    def status(self) -> dict:
        """获取系统状态"""
        return self.system.get_status()
    
    def hot_memories(self, limit: int = 10) -> List[dict]:
        """获取热门记忆"""
        # TODO: 实现热门记忆查询
        return []
    
    def recent_traces(self, limit: int = 5) -> List[dict]:
        """获取最近的检索轨迹"""
        from trace_recorder import TraceRecorder
        recorder = TraceRecorder()
        traces = recorder.get_traces(limit=limit)
        
        return [
            {
                "query": t.query,
                "event": t.event_type,
                "found": t.total_found,
                "duration_ms": t.duration_ms
            }
            for t in traces
        ]
    
    # ==================== 跨事件操作 ====================
    
    def find_related(self, query: str) -> List[dict]:
        """查找跨事件相关记忆"""
        candidates = self.merger.find_merge_candidates()
        
        # 过滤与查询相关的
        related = []
        for c in candidates:
            if query.lower() in c.event_type_1 or query.lower() in c.event_type_2:
                related.append({
                    "events": [c.event_type_1, c.event_type_2],
                    "similarity": c.similarity,
                    "benefit": c.merge_benefit
                })
        
        return related
    
    def merge_stats(self) -> dict:
        """获取合并统计"""
        return self.merger.get_merge_stats()
    
    # ==================== 辅助方法 ====================
    
    def _parse_event_type(self, event: str) -> EventType:
        """解析事件类型"""
        event_map = {
            "financial": EventType.FINANCIAL,
            "military": EventType.MILITARY,
            "ironclaw": EventType.IRONCLAW,
            "system": EventType.SYSTEM,
            "temp": EventType.TEMP
        }
        return event_map.get(event.lower(), EventType.TEMP)
    
    # ==================== CLI 接口 ====================
    
    def cli(self):
        """命令行交互"""
        print("\n🤖 记忆系统 CLI")
        print("=" * 40)
        print("命令: remember, recall, status, trace, quit")
        print("=" * 40)
        
        while True:
            try:
                cmd = input("\n> ").strip()
                
                if not cmd:
                    continue
                
                parts = cmd.split(maxsplit=2)
                action = parts[0].lower()
                
                if action == "quit" or action == "exit":
                    print("👋 再见！")
                    break
                
                elif action == "remember":
                    if len(parts) < 3:
                        print("用法: remember <topic> <content>")
                        continue
                    result = self.remember(parts[1], parts[2])
                    print(f"✅ {result['message']}")
                
                elif action == "recall":
                    query = parts[1] if len(parts) > 1 else ""
                    if not query:
                        print("用法: recall <query>")
                        continue
                    result = self.recall(query)
                    print(f"\n查询: {query}")
                    print(f"事件: {result['event_detected']}")
                    print(f"找到: {result['total_found']}条\n")
                    for i, r in enumerate(result['results'][:3], 1):
                        print(f"  {i}. {r.get('topic', 'N/A')}: {r.get('content', '')[:50]}...")
                
                elif action == "status":
                    status = self.status()
                    print(f"\nL2 热记忆: {status['L2']['hot']}条")
                    print(f"L2 温记忆: {status['L2']['warm']}条")
                    print(f"L2 冷记忆: {status['L2']['cold']}条")
                
                elif action == "trace":
                    traces = self.recent_traces(3)
                    for t in traces:
                        print(f"  {t['query']} → {t['found']}条 ({t['duration_ms']:.1f}ms)")
                
                else:
                    print(f"未知命令: {action}")
            
            except KeyboardInterrupt:
                print("\n👋 再见！")
                break
            except Exception as e:
                print(f"错误: {e}")


# ==================== 快捷函数 ====================

_api = None

def get_api() -> MemoryAPI:
    """获取全局 API 实例"""
    global _api
    if _api is None:
        _api = MemoryAPI()
    return _api


def remember(topic: str, content: str, **kwargs) -> dict:
    """快捷存储"""
    return get_api().remember(topic, content, **kwargs)


def recall(query: str, **kwargs) -> dict:
    """快捷搜索"""
    return get_api().recall(query, **kwargs)


# ==================== 测试 ====================

if __name__ == "__main__":
    print("=" * 60)
    print("记忆系统 API 测试")
    print("=" * 60)
    
    api = MemoryAPI()
    
    # 测试存储
    print("\n📍 测试存储:")
    result = api.remember("测试记忆", "这是一条测试记忆内容")
    print(f"   {result}")
    
    # 测试搜索
    print("\n📍 测试搜索:")
    result = api.recall("测试")
    print(f"   找到: {result['total_found']}条")
    
    # 测试状态
    print("\n📍 系统状态:")
    status = api.status()
    print(f"   {status}")
    
    print("\n✅ 测试完成")
    
    # 启动 CLI（可选）
    # api.cli()

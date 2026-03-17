#!/usr/bin/env python3
"""
l0_manager.py - L0瞬时记忆管理器
快速访问层，存储最近10分钟的记忆
"""

import datetime
import threading
import time
from typing import List, Dict, Any, Optional

class L0MemoryManager:
    """L0瞬时记忆管理器 - 纯内存，10分钟自动清理"""
    
    def __init__(self):
        self.memories = []  # 纯内存存储
        self.max_capacity = 20  # 最多20条
        self.retention_minutes = 10  # 保留10分钟
        self.cleanup_interval = 60  # 每分钟清理一次
        self.cleanup_thread = None
        self.running = False
        
        # 启动自动清理线程
        self.start_cleanup_thread()
    
    def start_cleanup_thread(self):
        """启动自动清理线程"""
        if not self.running:
            self.running = True
            self.cleanup_thread = threading.Thread(target=self._auto_cleanup, daemon=True)
            self.cleanup_thread.start()
            print("✅ L0自动清理线程已启动")
    
    def _auto_cleanup(self):
        """自动清理过期记忆"""
        while self.running:
            time.sleep(self.cleanup_interval)
            self.cleanup_expired()
    
    def stop_cleanup_thread(self):
        """停止自动清理线程"""
        self.running = False
        if self.cleanup_thread:
            self.cleanup_thread.join()
    
    def add_memory(self, content: str, category: str = "instant") -> Dict[str, Any]:
        """添加记忆到L0"""
        memory = {
            'id': len(self.memories) + 1,
            'content': content,
            'category': category,
            'timestamp': datetime.datetime.now().isoformat(),
            'datetime': datetime.datetime.now()
        }
        
        # 添加到列表
        self.memories.append(memory)
        
        # 检查容量限制
        if len(self.memories) > self.max_capacity:
            # 保留最新的记录
            self.memories = self.memories[-self.max_capacity:]
            print(f"🧹 L0已清理，保留最新{self.max_capacity}条")
        
        return {
            'success': True,
            'memory_id': memory['id'],
            'layer': 'L0',
            'total': len(self.memories)
        }
    
    def search_memory(self, query: str) -> List[Dict[str, Any]]:
        """搜索L0记忆（O(1)快速查找）"""
        results = []
        query_lower = query.lower()
        
        for memory in self.memories:
            if query_lower in memory['content'].lower():
                # 计算相关性
                content = memory['content'].lower()
                relevance = content.count(query_lower) / len(content.split())
                
                results.append({
                    'id': memory['id'],
                    'content': memory['content'],
                    'category': memory['category'],
                    'timestamp': memory['timestamp'],
                    'layer': 'L0',
                    'relevance': relevance
                })
        
        # 按相关性排序
        results.sort(key=lambda x: x['relevance'], reverse=True)
        
        return results
    
    def get_memory(self, memory_id: int) -> Optional[Dict[str, Any]]:
        """获取单条记忆"""
        for memory in self.memories:
            if memory['id'] == memory_id:
                return {
                    'id': memory['id'],
                    'content': memory['content'],
                    'category': memory['category'],
                    'timestamp': memory['timestamp']
                }
        return None
    
    def cleanup_expired(self):
        """清理过期记忆"""
        current_time = datetime.datetime.now()
        cutoff_time = current_time - datetime.timedelta(minutes=self.retention_minutes)
        
        initial_count = len(self.memories)
        
        # 过滤掉过期记忆
        self.memories = [
            m for m in self.memories 
            if m['datetime'] > cutoff_time
        ]
        
        cleaned_count = initial_count - len(self.memories)
        
        if cleaned_count > 0:
            print(f"🧹 L0清理了{cleaned_count}条过期记忆")
    
    def clear_all(self):
        """清空所有记忆"""
        count = len(self.memories)
        self.memories = []
        print(f"🧹 L0已清空{count}条记忆")
        return count
    
    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        return {
            'total_memories': len(self.memories),
            'max_capacity': self.max_capacity,
            'retention_minutes': self.retention_minutes,
            'usage_percent': len(self.memories) / self.max_capacity * 100 if self.max_capacity > 0 else 0
        }

# 创建全局实例
l0_manager = L0MemoryManager()

def test_l0():
    """测试L0记忆管理器"""
    print("=" * 40)
    print("🧪 测试L0瞬时记忆管理器")
    print("=" * 40)
    
    # 测试添加记忆
    print("\n测试1: 添加记忆")
    test_memories = [
        "当前对话上下文：用户正在询问记忆系统",
        "临时变量：session_id=12345",
        "快速查询：用户偏好设置"
    ]
    
    for content in test_memories:
        result = l0_manager.add_memory(content)
        print(f"✅ 添加成功: ID={result['memory_id']}")
    
    # 测试搜索
    print("\n测试2: 搜索记忆")
    results = l0_manager.search_memory("记忆")
    print(f"🔍 找到{len(results)}条结果")
    for r in results:
        print(f"   - {r['content'][:40]}...")
    
    # 测试统计
    print("\n测试3: 统计信息")
    stats = l0_manager.get_stats()
    print(f"📊 总记忆数: {stats['total_memories']}")
    print(f"   使用率: {stats['usage_percent']:.1f}%")
    print(f"   保留时间: {stats['retention_minutes']}分钟")
    
    print("\n✅ L0测试完成！")

if __name__ == "__main__":
    test_l0()
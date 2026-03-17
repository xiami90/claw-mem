#!/usr/bin/env python3
"""
memory_protocol.py - 记忆存储/检索协议
标准的记忆存储和检索接口
"""

import sys
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List

# 导入各层管理器
sys.path.insert(0, "/root/.openclaw/workspace/memory")
from l0_manager import L0MemoryManager
from l2_manager import L2MemoryManager
from vector_db import VectorDBManager
from smart_compress import L1Compressor
from priority_manager import PriorityManager
from result_filter import ResultFilter

class MemoryProtocol:
    """记忆存储/检索协议"""
    
    def __init__(self):
        # 初始化各层
        self.L0 = L0MemoryManager()
        self.L1 = L1Compressor()
        self.L2 = L2MemoryManager()
        self.L3 = VectorDBManager()
        
        # 初始化功能模块
        self.priority_manager = PriorityManager()
        self.result_filter = ResultFilter()
        
        print("📡 记忆协议系统初始化完成")
    
    def store_memory(self, topic: str, content: str, category: str = "general") -> str:
        """
        存储记忆协议
        STORED|<ID>|引力:<值>
        """
        try:
            # 1. 判断优先级
            priority_result = self.priority_manager.determine_priority(content, category)
            gravity = priority_result['gravity']
            priority_level = priority_result['priority']
            
            # 2. 存储到L2
            result_l2 = self.L2.add_memory(topic, content, category)
            memory_id = result_l2['memory_id']
            
            # 3. 同步到L3
            l3_synced = False
            if self.L3.chromadb_available:
                result_l3 = self.L3.add_memory(
                    content,
                    metadata={
                        'topic': topic,
                        'category': category,
                        'priority': priority_level,
                        'gravity': gravity,
                        'memory_id': memory_id
                    }
                )
                l3_synced = result_l3['success']
            
            # 4. 返回标准格式
            return f"STORED|{memory_id}|引力:{gravity:.2f}|L3同步:{l3_synced}"
            
        except Exception as e:
            return f"ERROR|存储失败: {str(e)}"
    
    def search_memory(self, query: str, limit: int = 5) -> str:
        """
        搜索记忆协议
        搜索策略（按优先级）:
        1. ChromaDB 语义搜索（向量数据库）
        2. Sentence-Transformers 语义检索（L2）
        3. 关键词匹配（回退）
        
        返回格式:
        FOUND|<数量>
        ID:<id>|引力:<值>|得分:<score>
        主题:<topic>
        内容:<content>
        ---
        ...
        """
        try:
            all_results = []
            
            # 1. ChromaDB 语义搜索（优先）
            if self.L3.chromadb_available:
                results_l3 = self.L3.search_memory(query, limit)
                all_results.extend(results_l3)
            
            # 2. L2 语义检索
            results_l2 = self.L2.search_memory(query, limit)
            all_results.extend(results_l2)
            
            # 3. L0 关键词匹配（回退）
            results_l0 = self.L0.search_memory(query)
            all_results.extend(results_l0)
            
            # 4. 去重
            all_results = self.result_filter.deduplicate_results(all_results)
            
            # 5. 过滤和排序
            filtered_results = self.result_filter.filter_results(all_results, limit)
            
            # 6. 格式化输出
            if not filtered_results:
                return "ERROR|未找到记忆"
            
            output = f"FOUND|{len(filtered_results)}\n"
            
            for i, result in enumerate(filtered_results):
                memory_id = result.get('id', '')
                gravity = result.get('gravity', 0.0)
                score = result.get('score', 0.0)
                topic = result.get('topic', result.get('content', '')[:20])
                content = result.get('content', '')
                
                output += f"ID:{memory_id}|引力:{gravity:.2f}|得分:{score:.2f}\n"
                output += f"主题:{topic}\n"
                output += f"内容:{content}\n"
                
                if i < len(filtered_results) - 1:
                    output += "---\n"
            
            return output
            
        except Exception as e:
            return f"ERROR|搜索失败: {str(e)}"
    
    def update_gravity(self, memory_id: int, delta: float = 0.2) -> str:
        """
        更新引力值协议
        UPDATED|<ID>|旧引力:<旧值>|新引力:<新值>
        """
        try:
            result = self.L2.update_gravity(memory_id, delta)
            
            if result['success']:
                old_gravity = result['old_gravity']
                new_gravity = result['new_gravity']
                return f"UPDATED|{memory_id}|旧引力:{old_gravity:.2f}|新引力:{new_gravity:.2f}"
            else:
                return f"ERROR|{result['message']}"
                
        except Exception as e:
            return f"ERROR|更新失败: {str(e)}"
    
    def delete_memory(self, memory_id: int) -> str:
        """
        删除记忆协议
        DELETED|<ID>
        """
        try:
            # 从L2删除
            result_l2 = self.L2.delete_memory(memory_id)
            
            # 从L3删除（如果需要）
            # 注意：L3使用UUID，不是整数ID
            
            if result_l2['success']:
                return f"DELETED|{memory_id}"
            else:
                return f"ERROR|{result_l2['message']}"
                
        except Exception as e:
            return f"ERROR|删除失败: {str(e)}"
    
    def compress_conversation(self, conversation: List[str] = None) -> str:
        """
        对话压缩协议
        COMPRESSED|<摘要文件路径>
        """
        try:
            # 触发压缩
            result = self.L1.trigger_compress()
            
            if result['success']:
                return f"COMPRESSED|/root/.openclaw/workspace/memory/l1_summary.txt|方法:{result['method']}"
            else:
                return f"ERROR|压缩失败"
                
        except Exception as e:
            return f"ERROR|压缩失败: {str(e)}"
    
    def get_system_status(self) -> str:
        """
        获取系统状态
        STATUS|<JSON格式状态>
        """
        try:
            stats_l0 = self.L0.get_stats()
            stats_l1 = self.L1.get_stats()
            stats_l2 = self.L2.get_stats()
            stats_l3 = self.L3.get_stats()
            
            status = {
                'L0': stats_l0,
                'L1': stats_l1,
                'L2': stats_l2,
                'L3': stats_l3,
                'summary': {
                    'total_memories': stats_l0['total_memories'] + stats_l2['total_memories'] + stats_l3.get('total_memories', 0),
                    'chromadb_available': stats_l3.get('available', False)
                }
            }
            
            return f"STATUS|{json.dumps(status, ensure_ascii=False)}"
            
        except Exception as e:
            return f"ERROR|获取状态失败: {str(e)}"

# 创建全局实例
memory_protocol = MemoryProtocol()

def test_memory_protocol():
    """测试记忆协议"""
    print("=" * 50)
    print("🧪 测试记忆存储/检索协议")
    print("=" * 50)
    
    # 测试1: 存储记忆
    print("\n测试1: 存储记忆")
    result = memory_protocol.store_memory(
        "测试记忆",
        "这是一个测试记忆，用于验证协议功能",
        "test"
    )
    print(f"📤 {result}")
    
    # 测试2: 搜索记忆
    print("\n测试2: 搜索记忆")
    result = memory_protocol.search_memory("测试", limit=3)
    print(f"📤 {result}")
    
    # 测试3: 更新引力值
    print("\n测试3: 更新引力值")
    result = memory_protocol.update_gravity(1, 0.2)
    print(f"📤 {result}")
    
    # 测试4: 系统状态
    print("\n测试4: 系统状态")
    result = memory_protocol.get_system_status()
    print(f"📤 {result[:200]}...")
    
    print("\n✅ 记忆协议测试完成！")

if __name__ == "__main__":
    test_memory_protocol()
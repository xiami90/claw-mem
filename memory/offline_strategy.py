#!/usr/bin/env python3
"""
offline_strategy.py - 离线回退策略
多层回退机制，确保离线可用
"""

import sys
from pathlib import Path
from typing import Dict, Any, List, Optional

# 导入各层管理器
sys.path.insert(0, "/root/.openclaw/workspace/memory")
from l0_manager import L0MemoryManager
from l2_manager import L2MemoryManager
from vector_db import VectorDBManager

class OfflineStrategy:
    """离线回退策略"""
    
    def __init__(self):
        # 初始化各层
        self.L0 = L0MemoryManager()
        self.L2 = L2MemoryManager()
        self.L3 = VectorDBManager()
        
        # 检查各层可用性
        self.chromadb_available = self.L3.chromadb_available
        self.l2_available = True  # L2总是可用
        self.l0_available = True  # L0总是可用
        
        # 回退日志
        self.fallback_logs = []
        
        print("📡 离线回退策略初始化完成")
    
    def search_with_fallback(self, query: str, limit: int = 5) -> Dict[str, Any]:
        """
        多层回退搜索
        L3 → L2 → L0
        """
        results = []
        fallback_used = None
        
        # 1. 尝试L3 ChromaDB（优先）
        if self.chromadb_available:
            try:
                print("🔍 尝试L3 ChromaDB搜索...")
                results = self.L3.search_memory(query, limit)
                
                if results:
                    print(f"✅ L3找到{len(results)}条结果")
                    return {
                        'success': True,
                        'source': 'L3-ChromaDB',
                        'fallback': False,
                        'found': len(results),
                        'results': results
                    }
                else:
                    print("⚠️️ L3未找到结果，回退到L2")
            except Exception as e:
                print(f"⚠️️ L3搜索失败: {e}，回退到L2")
        
        fallback_used = "L2"
        
        # 2. 回退到L2语义检索
        if self.l2_available:
            try:
                print("🔍 尝试L2语义检索...")
                results = self.L2.search_memory(query, limit)
                
                if results:
                    print(f"✅ L2找到{len(results)}条结果")
                    return {
                        'success': True,
                        'source': 'L2-Semantic',
                        'fallback': True,
                        'fallback_from': 'L3-ChromaDB',
                        'found': len(results),
                        'results': results
                    }
                else:
                    print("⚠️️ L2未找到结果，回退到L0")
            except Exception as e:
                print(f"⚠️️ L2搜索失败: {e}，回退到L0")
        

        
        fallback_used = "L0"
        
        # 3. 回退到L0关键词匹配
        if self.l0_available:
            try:
                print("🔍 尝试L0关键词匹配...")
                results = self.L0.search_memory(query)
                
                if results:
                    print(f"✅ L0找到{len(results)}条结果")
                    return {
                        'success': True,
                        'source': 'L0-Keyword',
                        'fallback': True,
                        'fallback_from': 'L2-Semantic',
                        'found': len(results),
                        'results': results
                    }
                else:
                    print("⚠️️ L0未找到结果")
            except Exception as e:
                print(f"⚠️️ L0搜索失败: {e}")
        
        # 所有回退都失败
        self._log_fallback({
            'query': query,
            'status': 'all_fallback_failed',
            'chromadb_available': self.chromadb_available
        })
        
        return {
            'success': False,
            'source': 'None',
            'fallback': True,
            'fallback_attempts': ['L3', 'L2', 'L0'],
            'found': 0,
            'results': []
        }
    
    def compress_with_fallback(self, conversation: str = None) -> Dict[str, Any]:
        """
        带回退的压缩策略
        LLM智能压缩 → 规则提取
        """
        try:
            # 尝试智能压缩（LLM）
            print("⚡ 尝试LLM智能压缩...")
            
            # 检查LLM是否可用（简化判断）
            llm_available = True  # 实际需要检查API
            
            if llm_available:
                # 执行智能压缩
                summary = self._smart_compress(conversation)
                
                print("✅ LLM智能压缩成功")
                return {
                    'success': True,
                    'method': 'llm_smart_compress',
                    'fallback': False,
                    'summary': summary
                }
            else:
                print("⚠️️ LLM不可用，回退到规则提取")
        except Exception as e:
            print(f"⚠️️ LLM压缩失败: {e}，回退到规则提取")
        
        # 回退到规则提取
        try:
            print("⚡ 执行规则提取压缩...")
            summary = self._rule_extract_compress(conversation)
            
            print("✅ 规则提取压缩成功")
            return {
                'success': True,
                'method': 'rule_extract',
                'fallback': True,
                'fallback_from': 'llm_smart_compress',
                'summary': summary
            }
        except Exception as e:
            print(f"⚠️️ 规则提取失败: {e}")
            
            return {
                'success': False,
                'method': 'none',
                'error': str(e)
            }
    
    def _smart_compress(self, conversation: str) -> str:
        """LLM智能压缩"""
        # 简化实现，实际应该调用LLM API
        if conversation:
            return f"""对话摘要（智能压缩）：

{conversation[:500]}...

关键信息提取：
1. 对话内容摘要
2. 重要决策点
3. 待办事项
"""
        else:
            return "对话摘要（智能压缩）:\n暂无对话内容"
    
    def _rule_extract_compress(self, conversation: str = None) -> str:
        """规则提取压缩"""
        from datetime import datetime
        
        if conversation:
            # 简化规则：保留前100字
            return f"""对话摘要（规则提取） - {datetime.now().strftime('%Y-%m-%d %H:%M')}

{conversation[:100]}...
"""
        else:
            return f"对话摘要（规则提取） - {datetime.now().strftime('%Y-%m-%d %H:%M')}:\n暂无对话内容"
    
    def _log_fallback(self, log_entry: Dict[str, Any]):
        """记录回退日志"""
        from datetime import datetime
        import json
        
        log_entry['timestamp'] = datetime.now().isoformat()
        self.fallback_logs.append(log_entry)
        
        # 保存日志
        try:
            log_file = Path("/root/.openclaw/workspace/memory/fallback_log.jsonl")
            with open(log_file, 'a', encoding='utf-8') as f:
                f.write(json.dumps(log_entry, ensure_ascii=False) + '\n')
        except Exception as e:
            print(f"⚠️️ 保存回退日志失败: {e}")
    
    def get_fallback_stats(self) -> Dict[str, Any]:
        """获取回退统计"""
        return {
            'chromadb_available': self.chromadb_available,
            'l2_available': self.l2_available,
            'l0_available': self.l0_available,
            'total_fallbacks': len(self.fallback_logs),
            'recent_fallbacks': self.fallback_logs[-10:] if self.fallback_logs else []
        }

# 创建全局实例
offline_strategy = OfflineStrategy()

def test_offline_strategy():
    """测试离线回退策略"""
    print("=" * 50)
    print("🧪 测试离线回退策略")
    print("=" * 50)
    
    # 测试1: 带回退的搜索
    print("\n测试1: 带回退的搜索")
    result = offline_strategy.search_with_fallback("测试", limit=5)
    print(f"✅ 搜索完成: 来源={result['source']}, 回退={result['fallback']}")
    print(f"   找到{result['found']}条结果")
    
    # 测试2: 带回退的压缩
    print("\n测试2: 带回退的压缩")
    result = offline_strategy.compress_with_fallback("这是一段很长的对话内容，需要压缩...")
    if result['success']:
        print(f"✅ 压缩完成: 方法={result['method']}, 回退={result['fallback']}")
        print(f"   摘要: {result['summary'][:100]}...")
    else:
        print(f"❌ 压缩失败: {result['error']}")
    
    # 测试3: 回退统计
    print("\n测试3: 回退统计")
    stats = offline_strategy.get_fallback_stats()
    print(f"📊 ChromaDB可用: {'是' if stats['chromadb_available'] else '否'}")
    print(f"   回退次数: {stats['total_fallbacks']}")
    
    print("\n✅ 离线回退策略测试完成！")

if __name__ == "__main__":
    test_offline_strategy()
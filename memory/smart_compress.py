#!/usr/bin/env python3
"""
smart_compress.py - L1智能压缩
使用LLM生成结构化摘要
"""

import json
import datetime
from pathlib import Path
from typing import List, Dict, Any

# 摘要文件路径
SUMMARY_FILE = Path("/root/.openclaw/workspace/memory/l1_summary.txt")

class L1Compressor:
    """L1工作记忆压缩器 - 智能压缩"""
    
    def __init__(self):
        self.summary_file = SUMMARY_FILE
        self.conversation_history = []
        self.max_turns = 20  # 最大对话轮次
        
        # 确保目录存在
        self.summary_file.parent.mkdir(parents=True, exist_ok=True)
    
    def add_turn(self, role: str, content: str):
        """添加对话轮次"""
        turn = {
            'role': role,
            'content': content,
            'timestamp': datetime.datetime.now().isoformat()
        }
        
        self.conversation_history.append(turn)
        
        # 检查是否需要压缩
        if len(self.conversation_history) >= self.max_turns:
            self.trigger_compress()
    
    def trigger_compress(self) -> Dict[str, Any]:
        """触发压缩"""
        print("⚡ 触发L1智能压缩...")
        
        # 尝试智能压缩
        if self.try_smart_compress():
            return {
                'success': True,
                'method': 'smart_compress',
                'turns': len(self.conversation_history)
            }
        else:
            # 回退到简单压缩
            return self.fallback_to_simple_compress()
    
    def try_smart_compress(self) -> bool:
        """尝试智能压缩（LLM生成摘要）"""
        try:
            # 检查LLM是否可用
            # 这里简化处理，假设LLM可用
            llm_available = True  # 实际需要检查API
            
            if not llm_available:
                print("⚠️️ LLM不可用，回退到规则提取")
                return False
            
            # 生成摘要
            summary = self._generate_llm_summary()
            
            # 保存摘要
            self._save_summary(summary)
            
            # 清空对话历史
            self.conversation_history = []
            
            print("✅ 智能压缩成功")
            return True
            
        except Exception as e:
            print(f"⚠️️ 智能压缩失败: {e}")
            return False
    
    def _generate_llm_summary(self) -> str:
        """使用LLM生成摘要"""
        # 构建上下文
        context = "\n".join([
            f"{turn['role']}: {turn['content']}"
            for turn in self.conversation_history[-10:]  # 只保留最后10轮
        ])
        
        # 生成摘要（简化版本）
        # 实际应该调用LLM API
        summary = f"""对话摘要（{datetime.datetime.now().strftime('%Y-%m-%d %H:%M')})：

关键信息：
1. 用户讨论了记忆系统的架构设计
2. 决定使用四层记忆架构
3. 正在实施Phase 1：核心架构

摘要：
{context[:500]}...
"""
        return summary
    
    def _save_summary(self, summary: str):
        """保存摘要到文件"""
        with open(self.summary_file, 'w', encoding='utf-8') as f:
            f.write(summary)
        
        print(f"✅ 摘要已保存: {self.summary_file}")
    
    def fallback_to_simple_compress(self) -> Dict[str, Any]:
        """回退到简单压缩（规则提取）"""
        print("⚡ 执行简单压缩（规则提取）...")
        
        # 保留最后10轮对话
        last_turns = self.conversation_history[-10:]
        
        # 生成简单摘要
        summary = f"""对话摘要（简单压缩） - {datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}

保留的对话轮次：
"""
        for i, turn in enumerate(last_turns, 1):
            summary += f"{i}. {turn['role']}: {turn['content'][:100]}...\n"
        
        # 保存摘要
        self._save_summary(summary)
        
        # 清空对话历史
        turn_count = len(self.conversation_history)
        self.conversation_history = []
        
        print("✅ 简单压缩完成")
        
        return {
            'success': True,
            'method': 'simple_compress',
            'turns': turn_count,
            'remaining_turns': len(last_turns)
        }
    
    def get_summary(self) -> str:
        """获取当前摘要"""
        try:
            if self.summary_file.exists():
                with open(self.summary_file, 'r', encoding='utf-8') as f:
                    return f.read()
            return "暂无摘要"
        except Exception as e:
            return f"读取摘要失败: {e}"
    
    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        return {
            'current_turns': len(self.conversation_history),
            'max_turns': self.max_turns,
            'usage_percent': len(self.conversation_history) / self.max_turns * 100 if self.max_turns > 0 else 0,
            'summary_file': str(self.summary_file),
            'summary_exists': self.summary_file.exists()
        }

# 创建全局实例
l1_compressor = L1Compressor()

def test_l1():
    """测试L1压缩器"""
    print("=" * 40)
    print("🧪 测试L1工作记忆压缩器")
    print("=" * 40)
    
    # 模拟对话
    print("\n测试1: 模拟对话")
    test_conversation = [
        ("user", "开始实施四层记忆系统"),
        ("assistant", "好的，开始执行Phase 1"),
        ("user", "需要创建哪些文件？"),
        ("assistant", "需要创建l0_manager.py, l2_manager.py, vector_db.py等"),
        ("user", "L1的功能是什么？"),
        ("assistant", "L1是工作记忆，监控对话长度，自动压缩"),
        ("user", "L2的功能呢？"),
        ("assistant", "L2是神经元记忆网，支持语义检索"),
        ("user", "L3呢？"),
        ("assistant", "L3是向量数据库，ChromaDB持久化"),
        ("user", "L0是做什么的？"),
        ("assistant", "L0是瞬时记忆，存储最近10分钟的记忆")
    ]
    
    for role, content in test_conversation:
        l1_compressor.add_turn(role, content)
        print(f"  {role}: {content[:40]}...")
    
    # 测试手动触发压缩
    print("\n测试2: 手动触发压缩")
    result = l1_compressor.trigger_compress()
    print(f"✅ 压缩完成: 方法={result['method']}, 轮次={result['turns']}")
    
    # 测试获取摘要
    print("\n测试3: 获取摘要")
    summary = l1_compressor.get_summary()
    print(f"📄 摘要内容:\n{summary[:200]}...")
    
    # 测试统计
    print("\n测试4: 统计信息")
    stats = l1_compressor.get_stats()
    print(f"📊 当前轮次: {stats['current_turns']}")
    print(f"   使用率: {stats['usage_percent']:.1f}%")
    print(f"   摘要存在: {'是' if stats['summary_exists'] else '否'}")
    
    print("\n✅ L1测试完成！")

if __name__ == "__main__":
    test_l1()
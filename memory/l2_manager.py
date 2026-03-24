#!/usr/bin/env python3
"""
l2_manager.py - L2神经元记忆网管理器
存储向量化记忆节点，支持语义检索
"""

import json
import datetime
import os
from pathlib import Path
from typing import List, Dict, Any, Optional

# 导入embedding引擎
from embedding_engine import embedding_engine

# 数据文件路径
DATA_FILE = Path("/root/.openclaw/workspace/memory/l2_memories.json")

class L2MemoryManager:
    """L2神经元记忆网管理器 - JSON持久化 + 向量索引"""
    
    def __init__(self):
        self.memories = []
        self.data_file = DATA_FILE
        
        # 确保目录存在
        self.data_file.parent.mkdir(parents=True, exist_ok=True)
        
        # 加载持久化数据
        self._load_data()
    
    def _load_data(self):
        """加载持久化数据"""
        try:
            if self.data_file.exists():
                with open(self.data_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.memories = data.get('memories', [])
                print(f"✅ 加载了{len(self.memories)}条L2记忆")
        except Exception as e:
            print(f"⚠️️ 加载数据失败: {e}")
            self.memories = []
    
    def _save_data(self):
        """保存持久化数据"""
        try:
            data = {
                'memories': self.memories,
                'last_saved': datetime.datetime.now().isoformat()
            }
            
            with open(self.data_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            
            return True
        except Exception as e:
            print(f"⚠️️ 保存数据失败: {e}")
            return False
    
    def _generate_vector(self, content: str) -> List[float]:
        """使用 embedding 引擎生成内容向量"""
        return embedding_engine.encode(content)
    
    def _calculate_similarity(self, vector1: List[float], vector2: List[float]) -> float:
        """计算向量相似度（余弦相似度）"""
        return embedding_engine.cosine_similarity(vector1, vector2)
    
    def _determine_priority(self, content: str, category: str = "") -> Dict[str, Any]:
        """判断优先级"""
        # 简化的优先级判断
        keywords = {
            "high": ["生日", "联系方式", "决策", "架构", "记住"],
            "medium": ["偏好", "项目", "团队", "工具", "会议"],
            "low": ["临时", "待办", "想法", "建议"]
        }
        
        # 检查关键词
        content_lower = content.lower()
        
        for level, words in keywords.items():
            if any(word in content_lower for word in words):
                if level == "high":
                    return {"level": "high", "gravity": 1.5}
                elif level == "medium":
                    return {"level": "medium", "gravity": 1.0}
        
        # 默认中优先级
        return {"level": "medium", "gravity": 1.0}
    
    def _detect_time_words(self, text: str) -> List[str]:
        """检测文本中的时间词"""
        import re
        time_patterns = [
            # 星期
            r'周[一二三四五六日天]', r'星期[一二三四五六日天]',
            # 今天/明天/昨天
            r'今[天日]', r'明[天日]', r'后[天日]', r'昨[天日]',
            # 刚/才/最近
            r'刚?[刚才]', r'刚才?', r'最近', r'刚才',
            # 早晚
            r'早[上中晚]', r'午[后前]', r'晚?[上中下]', r'中午',
            # 时间点
            r'\d+[点点小时时分秒]', r'\d+[分分钟]钟', r'\d+[秒秒钟]?',
            r'小?时', r'分钟', r'刚刚?', r'刚才?',
            # 现在/以前
            r'现[在的]', r'以[前后里]', r'曾[经]', r'过去',
        ]
        
        found = []
        for pattern in time_patterns:
            matches = re.findall(pattern, text)
            found.extend(matches)
        
        return found
    
    def _calculate_temporal_match(self, query_time_words: List[str], content: str) -> float:
        """计算时间匹配分数（含时态冲突检测）"""
        if not query_time_words:
            return 0.0
        
        content_lower = content.lower()
        query_lower = " ".join(query_time_words).lower()
        
        # 检测时态冲突
        # 查询"现在"但内容是"之前" → 负分
        has_now_in_query = any(w in query_lower for w in ['现在', '目前', '最新', '刚', '才'])
        has_before_in_content = any(w in content_lower for w in ['之前', '以前', '曾经', '过去', '曾'])
        
        if has_now_in_query and has_before_in_content:
            return -1.0  # 时态冲突，严重惩罚
        
        # 检测"之前"查询但内容是"现在"
        has_before_in_query = any(w in query_lower for w in ['之前', '以前', '曾经', '过去'])
        has_now_in_content = any(w in content_lower for w in ['现在', '目前', '最新', '刚', '才', '换了'])
        
        if has_before_in_query and has_now_in_content:
            return -0.5  # 时态冲突，轻度惩罚
        
        # 正常时间匹配
        content_time_words = self._detect_time_words(content)
        if not content_time_words:
            return 0.0
        
        overlap = set(query_time_words) & set(content_time_words)
        
        # 完全匹配
        if overlap == set(query_time_words):
            return 1.0
        
        # 部分匹配
        return len(overlap) / len(query_time_words) * 0.5
    
    def add_memory(self, topic: str, content: str, category: str = "general") -> Dict[str, Any]:
        """添加记忆到L2（自动去重：相同topic更新而非添加）"""
        # 判断优先级
        priority = self._determine_priority(content, category)
        
        # 检查是否已存在相同 topic 的记忆
        existing_idx = None
        for i, m in enumerate(self.memories):
            if m['topic'] == topic:
                existing_idx = i
                break
        
        now = datetime.datetime.now().isoformat()
        
        if existing_idx is not None:
            # 更新现有记忆
            old_memory = self.memories[existing_idx]
            self.memories[existing_idx] = {
                'id': old_memory['id'],
                'topic': topic,
                'content': content,
                'category': category,
                'gravity': priority['gravity'] + 0.2,  # 更新时增加引力
                'priority_level': priority['level'],
                'vector': self._generate_vector(content),
                'created': old_memory['created'],  # 保留创建时间
                'last_access': now,
                'access_count': old_memory.get('access_count', 0) + 1,
                'updated': now  # 标记更新时间
            }
            memory = self.memories[existing_idx]
            action = 'updated'
        else:
            # 创建新记忆
            memory = {
                'id': len(self.memories) + 1,
                'topic': topic,
                'content': content,
                'category': category,
                'gravity': priority['gravity'],
                'priority_level': priority['level'],
                'vector': self._generate_vector(content),
                'created': now,
                'last_access': now,
                'access_count': 0
            }
            self.memories.append(memory)
            action = 'added'
        
        # 保存数据
        self._save_data()
        
        return {
            'success': True,
            'memory_id': memory['id'],
            'layer': 'L2',
            'gravity': memory['gravity'],
            'priority_level': priority['level'],
            'total': len(self.memories),
            'action': action
        }
    
    def search_memory(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """语义搜索记忆（时态感知增强版）"""
        if not self.memories:
            return []
        
        # 检测查询中的时间词
        time_words_in_query = self._detect_time_words(query)
        has_temporal_query = bool(time_words_in_query)
        
        # 生成查询向量
        query_vector = self._generate_vector(query)
        
        # 计算相似度
        results = []
        for memory in self.memories:
            similarity = self._calculate_similarity(query_vector, memory['vector'])
            
            if similarity > 0.15:  # 降低阈值
                # 解析时间
                try:
                    last_access = datetime.datetime.fromisoformat(memory.get('last_access', memory.get('created', '2000-01-01')))
                    hours_old = (datetime.datetime.now() - last_access).total_seconds() / 3600
                    recency_factor = max(0.3, 1.0 - hours_old * 0.03)  # 每小时衰减3%
                except:
                    recency_factor = 0.7
                
                # 时态匹配分数
                temporal_score = 0.0
                if has_temporal_query:
                    # 如果查询有时态词，检查记忆内容是否也包含相关时间词
                    memory_content = memory.get('content', '') + memory.get('topic', '')
                    temporal_score = self._calculate_temporal_match(time_words_in_query, memory_content)
                
                # 综合评分 = 相似度 * 引力 + 时态匹配
                # 时态查询时：大幅提高 recency_factor，并加入时态匹配
                if has_temporal_query:
                    score = similarity * memory['gravity'] * recency_factor + temporal_score * 2.0
                else:
                    score = similarity * (memory['gravity'] + recency_factor * 0.5)
                
                results.append({
                    'id': memory['id'],
                    'topic': memory['topic'],
                    'content': memory['content'],
                    'category': memory['category'],
                    'gravity': memory['gravity'],
                    'similarity': similarity,
                    'recency_factor': recency_factor,
                    'score': score,
                    'created': memory.get('created'),
                    'last_access': memory.get('last_access'),
                    'layer': 'L2'
                })
        
        # 按综合评分排序
        results.sort(key=lambda x: x['score'], reverse=True)
        
        return results[:limit]
    
    def update_gravity(self, memory_id: int, delta: float = 0.2) -> Dict[str, Any]:
        """更新记忆引力值"""
        for memory in self.memories:
            if memory['id'] == memory_id:
                old_gravity = memory['gravity']
                memory['gravity'] += delta
                
                # 增加访问计数
                memory['access_count'] += 1
                memory['last_access'] = datetime.datetime.now().isoformat()
                
                # 保存数据
                self._save_data()
                
                return {
                    'success': True,
                    'memory_id': memory_id,
                    'old_gravity': old_gravity,
                    'new_gravity': memory['gravity']
                }
        
        return {'success': False, 'message': f'未找到记忆ID: {memory_id}'}
    
    def delete_memory(self, memory_id: int) -> Dict[str, Any]:
        """删除记忆"""
        for i, memory in enumerate(self.memories):
            if memory['id'] == memory_id:
                deleted = self.memories.pop(i)
                
                # 保存数据
                self._save_data()
                
                return {
                    'success': True,
                    'memory_id': memory_id,
                    'deleted': deleted
                }
        
        return {'success': False, 'message': f'未找到记忆ID: {memory_id}'}
    
    def apply_decay(self, decay_factor: float = 0.99) -> Dict[str, Any]:
        """应用衰减（引力值 × 0.99）"""
        initial_count = len(self.memories)
        
        # 衰减所有记忆
        self.memories = [
            m for m in self.memories 
            if m['gravity'] * decay_factor >= 0.1  # 移除低引力记忆
        ]
        
        # 更新引力值
        for memory in self.memories:
            memory['gravity'] *= decay_factor
        
        cleaned_count = initial_count - len(self.memories)
        
        # 保存数据
        self._save_data()
        
        return {
            'success': True,
            'decay_factor': decay_factor,
            'cleaned_count': cleaned_count,
            'remaining_count': len(self.memories)
        }
    
    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        if not self.memories:
            return {
                'total_memories': 0,
                'high_priority': 0,
                'medium_priority': 0,
                'low_priority': 0,
                'average_gravity': 0.0
            }
        
        high_count = sum(1 for m in self.memories if m.get('priority_level') == 'high')
        medium_count = sum(1 for m in self.memories if m.get('priority_level') == 'medium')
        low_count = sum(1 for m in self.memories if m.get('priority_level') == 'low')
        avg_gravity = sum(m['gravity'] for m in self.memories) / len(self.memories)
        
        return {
            'total_memories': len(self.memories),
            'high_priority': high_count,
            'medium_priority': medium_count,
            'low_priority': low_count,
            'average_gravity': avg_gravity,
            'data_file': str(self.data_file),
            'data_exists': self.data_file.exists()
        }

# 创建全局实例
l2_manager = L2MemoryManager()

def test_l2():
    """测试L2记忆管理器"""
    print("=" * 40)
    print("🧪 测试L2神经元记忆网管理器")
    print("=" * 40)
    
    # 测试添加记忆
    print("\n测试1: 添加记忆")
    test_memories = [
        ("用户偏好", "喜欢在早上处理重要工作，下午学习AI技术", "偏好"),
        ("投资决策", "坚持长期价值投资，关注基本面优秀的公司", "投资"),
        ("项目信息", "TradingAgents-CN项目正在部署中，需要配置API密钥", "项目"),
        ("个人信息", "生日是7月20日，联系方式在个人资料中", "个人")
    ]
    
    for topic, content, category in test_memories:
        result = l2_manager.add_memory(topic, content, category)
        print(f"✅ {topic}: 引力={result['gravity']}, 优先级={result['priority_level']}")
    
    # 测试搜索
    print("\n测试2: 语义搜索")
    query = "投资"
    results = l2_manager.search_memory(query)
    print(f"🔍 搜索'{query}': 找到{len(results)}条结果")
    for r in results:
        print(f"   - {r['topic']}: {r['content'][:40]}... (相关度:{r['score']:.2f})")
    
    # 测试引力更新
    print("\n测试3: 更新引力值")
    if len(l2_manager.memories) > 0:
        memory_id = l2_manager.memories[0]['id']
        result = l2_manager.update_gravity(memory_id, 0.2)
        if result['success']:
            print(f"✅ 记忆{memory_id}引力已从{result['old_gravity']}增强到{result['new_gravity']}")
    
    # 测试统计
    print("\n测试4: 统计信息")
    stats = l2_manager.get_stats()
    print(f"📊 总记忆数: {stats['total_memories']}")
    print(f"   高优先级: {stats['high_priority']}")
    print(f"   中优先级: {stats['medium_priority']}")
    print(f"   低优先级: {stats['low_priority']}")
    print(f"   平均引力: {stats['average_gravity']:.2f}")
    
    print("\n✅ L2测试完成！")

if __name__ == "__main__":
    test_l2()
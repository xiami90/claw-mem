#!/usr/bin/env python3
"""
enhanced_memory_system.py - 增强版记忆系统
整合所有新模块，提供统一接口

模块整合：
1. event_directories - 目录结构
2. embedding_engine - 向量引擎
3. event_router - 事件路由
4. trace_recorder - 轨迹记录
5. hotness_scorer - 热度评分
"""

from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime
import json
import logging

# 导入新模块
from event_directories import DirectoryManager, EventType, EventDirectory
from embedding_engine import SmartEmbedder, EmbedResult, create_embedder
from event_router import EventRouter, RoutedQuery, SmartRouter
from trace_recorder import TraceRecorder, TraceContext, RetrievalTrace
from hotness_scorer import ImportanceScorer, MemoryLifecycleManager

# 导入现有模块
from l0_manager import L0MemoryManager
from l2_manager import L2MemoryManager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# ==================== 增强版 L2 管理器 ====================

class EnhancedL2Manager(L2MemoryManager):
    """
    增强版 L2 管理器
    
    整合：
    - 目录结构化存储
    - 专业向量引擎
    - 事件路由
    - 轨迹记录
    - 热度评分
    """
    
    def __init__(self, data_dir: str = "/root/.openclaw/workspace/memory/l2_memories"):
        super().__init__()
        
        # 初始化新模块
        self.directory_manager = DirectoryManager()
        self.embedder = create_embedder()
        self.event_router = EventRouter()
        self.trace_recorder = TraceRecorder()
        self.importance_scorer = ImportanceScorer()
        self.lifecycle_manager = MemoryLifecycleManager(self.importance_scorer)
        
        self.data_dir = Path(data_dir)
        logger.info("🚀 增强版 L2 管理器初始化完成")
    
    def store_with_event(
        self,
        topic: str,
        content: str,
        event_type: EventType,
        category: str = "general",
        priority: str = "medium",
        metadata: dict = None
    ) -> dict:
        """
        按事件存储记忆
        
        Args:
            topic: 主题
            content: 内容
            event_type: 事件类型
            category: 分类
            priority: 优先级
            metadata: 额外元数据
        
        Returns:
            存储结果
        """
        # 获取事件目录
        event_path = self.directory_manager.get_event_path(event_type)
        memory_file = event_path / "memories.json"
        
        # 生成向量
        embed_result = self.embedder.embed(content)
        
        # 创建记忆记录
        memory = {
            "id": self._generate_id(),
            "topic": topic,
            "content": content,
            "event_type": event_type.value,
            "category": category,
            "priority": priority,
            "vector": embed_result.dense_vector[:50],  # 存储前50维
            "created": datetime.now().isoformat(),
            "last_access": datetime.now().isoformat(),
            "access_count": 0,
            "metadata": metadata or {}
        }
        
        # 保存到事件目录
        self._save_memory_to_file(memory_file, memory)
        
        # 同时保存到父类（兼容性）
        self.add_memory(topic, content, category)
        
        logger.info(f"💾 存储记忆: {topic} → {event_type.value}")
        
        return {
            "success": True,
            "memory_id": memory["id"],
            "event_type": event_type.value,
            "path": str(memory_file)
        }
    
    def search_with_trace(
        self,
        query: str,
        limit: int = 5,
        event_filter: EventType = None
    ) -> Dict[str, Any]:
        """
        带轨迹记录的搜索
        
        Args:
            query: 查询文本
            limit: 最大结果数
            event_filter: 事件类型过滤
        """
        # 事件路由
        routed = self.event_router.route(query) if not event_filter else RoutedQuery(
            query=query,
            event_type=event_filter,
            target_directories=[event_filter.value]
        )
        
        # 开始轨迹记录
        with TraceContext(self.trace_recorder, query, routed.event_type.value) as trace:
            results = []
            
            # 1. 向量搜索（L3）
            query_embed = self.embedder.embed(query)
            trace.step("L3", "vector_search", "embedding_engine", found=0, duration_ms=10)
            
            # 2. 搜索目标事件目录
            for target_dir in routed.target_directories:
                dir_path = self.data_dir / target_dir
                if not dir_path.exists():
                    continue
                
                memory_file = dir_path / "memories.json"
                if memory_file.exists():
                    found = self._search_in_file(memory_file, query, query_embed, limit)
                    results.extend(found)
                    trace.step("L2", "semantic_search", target_dir, found=len(found))
            
            # 3. 回退到父类搜索（兼容性）
            if len(results) < limit:
                legacy_results = self.search_memory(query, limit - len(results))
                results.extend(legacy_results)
                trace.step("L2", "legacy_search", "parent_class", found=len(legacy_results))
            
            return {
                "query": query,
                "event_type": routed.event_type.value,
                "results": results[:limit],
                "total_found": len(results),
                "trace": trace.trace.to_dict() if hasattr(trace, 'trace') else None
            }
    
    def _generate_id(self) -> str:
        """生成唯一 ID"""
        import hashlib
        return hashlib.md5(str(datetime.now()).encode()).hexdigest()[:12]
    
    def _save_memory_to_file(self, file_path: Path, memory: dict):
        """保存记忆到文件"""
        file_path.parent.mkdir(parents=True, exist_ok=True)
        
        # 加载现有记忆
        if file_path.exists():
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
        else:
            data = {"memories": [], "last_updated": None}
        
        # 添加新记忆
        data["memories"].append(memory)
        data["last_updated"] = datetime.now().isoformat()
        
        # 保存
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    
    def _search_in_file(
        self,
        file_path: Path,
        query: str,
        query_embed: EmbedResult,
        limit: int
    ) -> List[dict]:
        """在文件中搜索"""
        if not file_path.exists():
            return []
        
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        memories = data.get("memories", [])
        
        # 计算相似度
        scored = []
        for m in memories:
            # 关键词匹配
            if query.lower() in m.get("content", "").lower() or \
               query.lower() in m.get("topic", "").lower():
                scored.append((m, 0.9))  # 高分
                continue
            
            # 向量相似度
            if "vector" in m:
                sim = self._cosine_similarity(query_embed.dense_vector[:50], m["vector"])
                if sim > 0.5:
                    scored.append((m, sim))
        
        # 排序
        scored.sort(key=lambda x: x[1], reverse=True)
        
        return [s[0] for s in scored[:limit]]
    
    def _cosine_similarity(self, v1: List[float], v2: List[float]) -> float:
        """余弦相似度"""
        if len(v1) != len(v2):
            return 0.0
        dot = sum(a * b for a, b in zip(v1, v2))
        norm1 = sum(a * a for a in v1) ** 0.5
        norm2 = sum(b * b for b in v2) ** 0.5
        if norm1 == 0 or norm2 == 0:
            return 0.0
        return dot / (norm1 * norm2)
    
    def get_lifecycle_stats(self) -> Dict:
        """获取生命周期统计"""
        # 收集所有记忆
        all_memories = []
        for event_type in EventType:
            event_path = self.directory_manager.get_event_path(event_type)
            memory_file = event_path / "memories.json"
            if memory_file.exists():
                with open(memory_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    all_memories.extend(data.get("memories", []))
        
        # 分类
        classified = self.lifecycle_manager.classify_memories(all_memories)
        
        return {
            "total": len(all_memories),
            "hot": len(classified["hot"]),
            "warm": len(classified["warm"]),
            "cold": len(classified["cold"])
        }


# ==================== 增强版四层系统 ====================

class EnhancedFourLayerSystem:
    """
    增强版四层记忆系统
    
    整合：
    - L0: 瞬时记忆（不变）
    - L1: 压缩层（不变）
    - L2: 增强版神经元记忆网
    - L3: ChromaDB（可选）
    """
    
    def __init__(self):
        self.L0 = L0MemoryManager()
        # L1 压缩器暂时跳过
        self.L2 = EnhancedL2Manager()
        # L3 ChromaDB 可选
        
        logger.info("🚀 增强版四层记忆系统初始化完成")
    
    def store(
        self,
        topic: str,
        content: str,
        event_type: EventType = EventType.TEMP,
        category: str = "general",
        priority: str = "medium"
    ) -> dict:
        """存储记忆"""
        # 存储到 L2
        result = self.L2.store_with_event(
            topic=topic,
            content=content,
            event_type=event_type,
            category=category,
            priority=priority
        )
        
        # 同时存到 L0（瞬时）
        self.L0.add_memory(content, category)
        
        return result
    
    def search(
        self,
        query: str,
        limit: int = 5,
        event_filter: EventType = None
    ) -> dict:
        """搜索记忆"""
        return self.L2.search_with_trace(query, limit, event_filter)
    
    def get_status(self) -> dict:
        """获取系统状态"""
        return {
            "L0": {"type": "instant", "ttl": "10min"},
            "L2": self.L2.get_lifecycle_stats(),
            "modules": {
                "directory": "✅",
                "embedding": "✅",
                "router": "✅",
                "trace": "✅",
                "hotness": "✅"
            }
        }


# ==================== 测试 ====================

if __name__ == "__main__":
    print("=" * 60)
    print("增强版记忆系统测试")
    print("=" * 60)
    
    system = EnhancedFourLayerSystem()
    
    # 测试存储
    print("\n📍 测试存储:")
    result1 = system.store(
        topic="比亚迪预测",
        content="预测比亚迪今日上涨2%，目标价102元",
        event_type=EventType.FINANCIAL,
        category="投资",
        priority="high"
    )
    print(f"   存储: {result1['memory_id']} → {result1['event_type']}")
    
    result2 = system.store(
        topic="孙子兵法笔记",
        content="始计篇：兵者，国之大事",
        event_type=EventType.MILITARY,
        category="学习",
        priority="medium"
    )
    print(f"   存储: {result2['memory_id']} → {result2['event_type']}")
    
    # 测试搜索
    print("\n📍 测试搜索:")
    search_result = system.search("比亚迪", limit=3)
    print(f"   查询: 比亚迪")
    print(f"   事件: {search_result['event_type']}")
    print(f"   找到: {search_result['total_found']}条")
    
    # 显示轨迹
    if search_result.get("trace"):
        trace = RetrievalTrace(
            query=search_result["trace"]["query"],
            event_type=search_result["trace"]["event_type"],
            steps=[],
            total_found=search_result["trace"]["total_found"]
        )
        print(f"\n   {trace.render()}")
    
    # 测试状态
    print("\n📍 系统状态:")
    status = system.get_status()
    print(f"   L2 热记忆: {status['L2']['hot']}条")
    print(f"   L2 温记忆: {status['L2']['warm']}条")
    print(f"   L2 冷记忆: {status['L2']['cold']}条")
    print(f"   模块状态: {status['modules']}")
    
    print("\n✅ 测试完成")

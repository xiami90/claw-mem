#!/usr/bin/env python3
"""
cross_event_merger.py - 跨事件合并算法
借鉴 OpenViking 的碎片整理思路

功能：
1. 检测跨事件相关记忆
2. 智能合并碎片
3. 保持事件隔离边界
"""

from typing import List, Dict, Any, Set, Tuple
from dataclasses import dataclass
from datetime import datetime
import logging
from pathlib import Path
import json

from event_directories import EventType
from embedding_engine import SmartEmbedder
from hotness_scorer import ImportanceScorer

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class MergeCandidate:
    """合并候选"""
    memory_id_1: str
    memory_id_2: str
    event_type_1: str
    event_type_2: str
    similarity: float
    merge_benefit: float  # 合并收益


class CrossEventMerger:
    """
    跨事件合并器
    
    功能：
    1. 检测语义相似但分布在不同事件的记忆
    2. 评估合并收益
    3. 执行安全合并（不破坏隔离）
    """
    
    SIMILARITY_THRESHOLD = 0.85  # 相似度阈值
    MIN_BENEFIT = 0.3            # 最小合并收益
    
    def __init__(self, data_dir: str = "/root/.openclaw/workspace/memory/l2_memories"):
        self.data_dir = Path(data_dir)
        self.embedder = SmartEmbedder()
        self.scorer = ImportanceScorer()
    
    def find_merge_candidates(self) -> List[MergeCandidate]:
        """查找合并候选"""
        candidates = []
        
        # 收集所有记忆
        all_memories = self._collect_all_memories()
        
        # 按事件类型分组
        by_event: Dict[str, List[dict]] = {}
        for mem in all_memories:
            event_type = mem.get("event_type", "unknown")
            if event_type not in by_event:
                by_event[event_type] = []
            by_event[event_type].append(mem)
        
        # 跨事件比较
        event_types = list(by_event.keys())
        for i, event_1 in enumerate(event_types):
            for event_2 in event_types[i+1:]:
                for mem_1 in by_event[event_1]:
                    for mem_2 in by_event[event_2]:
                        similarity = self._calculate_similarity(mem_1, mem_2)
                        
                        if similarity >= self.SIMILARITY_THRESHOLD:
                            benefit = self._calculate_merge_benefit(mem_1, mem_2)
                            
                            if benefit >= self.MIN_BENEFIT:
                                candidates.append(MergeCandidate(
                                    memory_id_1=mem_1["id"],
                                    memory_id_2=mem_2["id"],
                                    event_type_1=event_1,
                                    event_type_2=event_2,
                                    similarity=similarity,
                                    merge_benefit=benefit
                                ))
        
        # 按收益排序
        candidates.sort(key=lambda x: x.merge_benefit, reverse=True)
        
        logger.info(f"🔍 发现 {len(candidates)} 个合并候选")
        return candidates
    
    def _collect_all_memories(self) -> List[dict]:
        """收集所有记忆"""
        memories = []
        
        for event_dir in self.data_dir.iterdir():
            if event_dir.is_dir():
                memory_file = event_dir / "memories.json"
                if memory_file.exists():
                    with open(memory_file, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        for mem in data.get("memories", []):
                            mem["event_type"] = event_dir.name
                            memories.append(mem)
        
        return memories
    
    def _calculate_similarity(self, mem_1: dict, mem_2: dict) -> float:
        """计算相似度"""
        # 向量相似度
        if "vector" in mem_1 and "vector" in mem_2:
            v1, v2 = mem_1["vector"], mem_2["vector"]
            if len(v1) == len(v2):
                dot = sum(a * b for a, b in zip(v1, v2))
                norm1 = sum(a * a for a in v1) ** 0.5
                norm2 = sum(b * b for b in v2) ** 0.5
                if norm1 > 0 and norm2 > 0:
                    return dot / (norm1 * norm2)
        
        # 关键词重叠（回退）
        words_1 = set(mem_1.get("content", "").lower().split())
        words_2 = set(mem_2.get("content", "").lower().split())
        if words_1 and words_2:
            overlap = len(words_1 & words_2)
            union = len(words_1 | words_2)
            return overlap / union if union > 0 else 0.0
        
        return 0.0
    
    def _calculate_merge_benefit(self, mem_1: dict, mem_2: dict) -> float:
        """计算合并收益"""
        # 收益因素：
        # 1. 两者都是冷记忆 → 合并收益高
        # 2. 内容互补 → 收益高
        # 3. 时间接近 → 收益高
        
        benefit = 0.0
        
        # 冷记忆检测
        access_1 = mem_1.get("access_count", 0)
        access_2 = mem_2.get("access_count", 0)
        if access_1 < 3 and access_2 < 3:
            benefit += 0.3
        
        # 主题相关性
        topic_1 = set(mem_1.get("topic", "").lower().split())
        topic_2 = set(mem_2.get("topic", "").lower().split())
        if topic_1 and topic_2 and not (topic_1 & topic_2):
            benefit += 0.2  # 主题互补
        
        # 时间接近性
        created_1 = mem_1.get("created", "")
        created_2 = mem_2.get("created", "")
        if created_1 and created_2:
            try:
                t1 = datetime.fromisoformat(created_1)
                t2 = datetime.fromisoformat(created_2)
                hours_diff = abs((t1 - t2).total_seconds() / 3600)
                if hours_diff < 24:
                    benefit += 0.3
                elif hours_diff < 168:  # 一周内
                    benefit += 0.1
            except:
                pass
        
        return benefit
    
    def merge_memories(self, candidate: MergeCandidate) -> dict:
        """
        执行合并
        
        注意：不真正移动记忆，只创建关联链接
        """
        # 加载两个记忆
        mem_1 = self._load_memory(candidate.event_type_1, candidate.memory_id_1)
        mem_2 = self._load_memory(candidate.event_type_2, candidate.memory_id_2)
        
        if not mem_1 or not mem_2:
            return {"success": False, "reason": "记忆不存在"}
        
        # 创建合并后的摘要
        merged_summary = {
            "id": f"merged_{candidate.memory_id_1[:8]}_{candidate.memory_id_2[:8]}",
            "source_1": {
                "id": candidate.memory_id_1,
                "event_type": candidate.event_type_1
            },
            "source_2": {
                "id": candidate.memory_id_2,
                "event_type": candidate.event_type_2
            },
            "similarity": candidate.similarity,
            "benefit": candidate.merge_benefit,
            "merged_at": datetime.now().isoformat(),
            "combined_topic": f"{mem_1.get('topic', '')} + {mem_2.get('topic', '')}",
            "combined_content": f"{mem_1.get('content', '')}\n---\n{mem_2.get('content', '')}"
        }
        
        # 保存合并记录（不删除原记忆）
        merge_file = self.data_dir / "_system" / "merges.json"
        self._append_merge_record(merge_file, merged_summary)
        
        logger.info(f"✅ 合并完成: {candidate.memory_id_1[:8]} + {candidate.memory_id_2[:8]}")
        
        return {
            "success": True,
            "merge_id": merged_summary["id"],
            "preserved_original": True
        }
    
    def _load_memory(self, event_type: str, memory_id: str) -> dict:
        """加载记忆"""
        memory_file = self.data_dir / event_type / "memories.json"
        if not memory_file.exists():
            return None
        
        with open(memory_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        for mem in data.get("memories", []):
            if mem.get("id") == memory_id:
                return mem
        
        return None
    
    def _append_merge_record(self, file_path: Path, record: dict):
        """追加合并记录"""
        file_path.parent.mkdir(parents=True, exist_ok=True)
        
        if file_path.exists():
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
        else:
            data = {"merges": [], "last_updated": None}
        
        data["merges"].append(record)
        data["last_updated"] = datetime.now().isoformat()
        
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    
    def get_merge_stats(self) -> dict:
        """获取合并统计"""
        merge_file = self.data_dir / "_system" / "merges.json"
        
        if not merge_file.exists():
            return {"total_merges": 0}
        
        with open(merge_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        merges = data.get("merges", [])
        
        # 按事件对统计
        by_event_pair = {}
        for m in merges:
            pair = f"{m['source_1']['event_type']}-{m['source_2']['event_type']}"
            by_event_pair[pair] = by_event_pair.get(pair, 0) + 1
        
        return {
            "total_merges": len(merges),
            "by_event_pair": by_event_pair,
            "last_merged": data.get("last_updated")
        }


# ==================== 测试 ====================

if __name__ == "__main__":
    print("=" * 60)
    print("跨事件合并测试")
    print("=" * 60)
    
    merger = CrossEventMerger()
    
    # 查找候选
    print("\n📍 查找合并候选:")
    candidates = merger.find_merge_candidates()
    
    print(f"   发现 {len(candidates)} 个候选")
    
    for c in candidates[:3]:
        print(f"   - {c.event_type_1}/{c.memory_id_1[:8]} ↔ {c.event_type_2}/{c.memory_id_2[:8]}")
        print(f"     相似度: {c.similarity:.2f}, 收益: {c.merge_benefit:.2f}")
    
    # 执行合并
    if candidates:
        print("\n📍 执行合并:")
        result = merger.merge_memories(candidates[0])
        print(f"   结果: {result}")
    
    # 统计
    print("\n📍 合并统计:")
    stats = merger.get_merge_stats()
    print(f"   总合并数: {stats['total_merges']}")
    
    print("\n✅ 测试完成")
